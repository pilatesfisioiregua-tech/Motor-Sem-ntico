#!/usr/bin/env python3
"""
Agente semántico de Gmail.
Lee el contenido real de los emails, los analiza con LLM,
y propone/ejecuta reorganización por semántica (no por remitente).

Uso:
  python3 gmail_semantic_agent.py --analyze                     # Analizar inbox
  python3 gmail_semantic_agent.py --analyze --todo              # Analizar TODO el correo
  python3 gmail_semantic_agent.py --analyze --query "after:2026/01/01"  # Rango custom
  python3 gmail_semantic_agent.py --map                         # Mapa semántico
  python3 gmail_semantic_agent.py --propose                     # Propuesta de etiquetas
  python3 gmail_semantic_agent.py --execute                     # Aplicar etiquetas
  python3 gmail_semantic_agent.py --account pilates             # Solo una cuenta
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
DATA_DIR = SCRIPT_DIR / "semantic_data"

OPENROUTER_KEY = "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"
ANALYSIS_MODEL = "deepseek/deepseek-chat-v3-0324"
PROPOSAL_MODEL = "deepcogito/cogito-v2.1-671b"

ACCOUNTS = {
    "gurufe": {
        "account": "gurufe@gmail.com",
        "token_file": "token_semantic_gurufe.json",
    },
    "pilates": {
        "account": "pilatesfisioiregua@gmail.com",
        "token_file": "token_semantic_pilates.json",
    },
}

MAX_EMAIL_CHARS = 2000  # Max chars of email body to send to LLM
BATCH_SIZE = 50         # Emails per batch


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def authenticate(account_key: str) -> Any:
    config = ACCOUNTS[account_key]
    token_path = SCRIPT_DIR / config["token_file"]
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: No se encuentra {CREDENTIALS_FILE}")
                sys.exit(1)
            print(f"\n  Autenticando {config['account']}...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── GMAIL HELPERS ────────────────────────────────────────────────────────────

def search_messages(service: Any, query: str, max_results: int = 5000) -> List[dict]:
    """Search Gmail messages. Returns list of {id, threadId}."""
    messages = []
    page_token = None

    while len(messages) < max_results:
        kwargs = {"userId": "me", "q": query, "maxResults": min(500, max_results - len(messages))}
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.users().messages().list(**kwargs).execute()
        messages.extend(results.get("messages", []))

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return messages[:max_results]


def get_message_content(service: Any, message_id: str) -> Optional[dict]:
    """Get full message with headers and body text."""
    try:
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    except Exception:
        return None

    headers = {}
    for h in msg.get("payload", {}).get("headers", []):
        headers[h["name"]] = h["value"]

    # Extract body text
    body = extract_body(msg.get("payload", {}))

    internal_date = int(msg.get("internalDate", 0)) / 1000
    msg_date = datetime.fromtimestamp(internal_date)

    return {
        "id": message_id,
        "threadId": msg.get("threadId", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": msg_date.isoformat(),
        "labels": msg.get("labelIds", []),
        "snippet": msg.get("snippet", ""),
        "body": body[:MAX_EMAIL_CHARS] if body else "",
        "size": msg.get("sizeEstimate", 0),
        "has_attachment": any(
            p.get("filename") for p in _flatten_parts(msg.get("payload", {}))
        ),
    }


def extract_body(payload: dict) -> str:
    """Extract plain text body from email payload."""
    parts = _flatten_parts(payload)

    # Prefer text/plain
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                except Exception:
                    pass

    # Fallback to text/html (strip tags)
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    return re.sub(r'<[^>]+>', ' ', html)  # Strip HTML tags
                except Exception:
                    pass

    # Last resort: body data directly
    data = payload.get("body", {}).get("data", "")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            pass

    return ""


def _flatten_parts(payload: dict) -> List[dict]:
    """Recursively flatten MIME parts."""
    parts = []
    if "parts" in payload:
        for part in payload["parts"]:
            parts.extend(_flatten_parts(part))
    else:
        parts.append(payload)
    return parts


def get_labels(service: Any) -> Dict[str, str]:
    """Returns {label_name: label_id}."""
    results = service.users().labels().list(userId="me").execute()
    return {l["name"]: l["id"] for l in results.get("labels", [])}


def create_label(service: Any, name: str) -> str:
    """Create a label. Returns label ID."""
    body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    result = service.users().labels().create(userId="me", body=body).execute()
    return result["id"]


def batch_modify(service: Any, msg_ids: List[str], add_labels: List[str] = None, remove_labels: List[str] = None) -> None:
    """Batch modify messages."""
    for i in range(0, len(msg_ids), 1000):
        chunk = msg_ids[i:i + 1000]
        body = {"ids": chunk}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels
        service.users().messages().batchModify(userId="me", body=body).execute()
        time.sleep(0.3)


# ─── LLM ──────────────────────────────────────────────────────────────────────

def call_llm(model: str, system: str, user_msg: str, max_tokens: int = 500) -> Optional[str]:
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    })

    result = subprocess.run(
        ["curl", "-s", "https://openrouter.ai/api/v1/chat/completions",
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {OPENROUTER_KEY}",
         "-d", payload],
        capture_output=True, text=True, timeout=120,
    )

    try:
        data = json.loads(result.stdout)
        content = data["choices"][0]["message"]["content"]
        return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    except Exception:
        return None


# ─── PHASE 1+2: ANALYZE ──────────────────────────────────────────────────────

ANALYSIS_SYSTEM = """Eres un asistente de organización de email. Analiza este correo y responde SOLO en JSON:

{
  "categoria": "factura|newsletter|personal|trabajo|banco|seguridad|viaje|compra|suscripcion|notificacion|formacion|legal|spam|otro",
  "tema": "tema en 3-5 palabras",
  "tags": ["tag1", "tag2", "tag3"],
  "importancia": "alta|media|baja",
  "accion": "archivar|conservar|eliminar",
  "resumen": "una frase sobre qué trata el email"
}

Criterios de importancia:
- alta: facturas, contratos, reservas activas, alertas seguridad, comunicación personal directa
- media: notificaciones de servicio, recibos, actualizaciones de cuenta
- baja: newsletters, promos, marketing, spam"""


def analyze_emails(account_key: str, query: str, max_emails: int) -> None:
    """Crawl and analyze emails with LLM."""
    config = ACCOUNTS[account_key]
    account = config["account"]
    data_file = DATA_DIR / f"email_analysis_{account_key}.json"

    print(f"\n{'='*60}")
    print(f" Análisis semántico Gmail: {account}")
    print(f" Query: {query}")
    print(f"{'='*60}")

    service = authenticate(account_key)

    # Load existing
    existing = {}
    if data_file.exists():
        with open(data_file) as f:
            existing = json.load(f)
        print(f"  Análisis previo: {len(existing)} emails")

    # Search
    print(f"  Buscando emails...")
    messages = search_messages(service, query, max_results=max_emails)
    print(f"  Encontrados: {len(messages)} emails")

    new_count = 0
    skip_count = 0
    error_count = 0

    for i, msg_ref in enumerate(messages, 1):
        msg_id = msg_ref["id"]

        if msg_id in existing:
            skip_count += 1
            continue

        # Get full message
        msg = get_message_content(service, msg_id)
        if not msg:
            error_count += 1
            continue

        # Build prompt
        body_preview = msg["body"][:MAX_EMAIL_CHARS] if msg["body"] else msg["snippet"]
        prompt = (
            f"De: {msg['from']}\n"
            f"Para: {msg['to']}\n"
            f"Asunto: {msg['subject']}\n"
            f"Fecha: {msg['date']}\n"
            f"Adjuntos: {'sí' if msg['has_attachment'] else 'no'}\n\n"
            f"Contenido:\n{body_preview}"
        )

        subject_short = (msg['subject'] or 'sin asunto')[:50]
        print(f"  [{i}/{len(messages)}] {subject_short}...", end=" ", flush=True)

        llm_response = call_llm(ANALYSIS_MODEL, ANALYSIS_SYSTEM, prompt)

        if llm_response:
            try:
                json_match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
                analysis = json.loads(json_match.group()) if json_match else {"categoria": "otro", "tags": [], "resumen": llm_response[:100]}
            except (json.JSONDecodeError, AttributeError):
                analysis = {"categoria": "otro", "tags": [], "resumen": llm_response[:100]}

            existing[msg_id] = {
                "from": msg["from"],
                "to": msg["to"],
                "subject": msg["subject"],
                "date": msg["date"],
                "labels": msg["labels"],
                "threadId": msg["threadId"],
                "has_attachment": msg["has_attachment"],
                "size": msg["size"],
                "analysis": analysis,
            }
            new_count += 1
            cat = analysis.get("categoria", "?")
            imp = analysis.get("importancia", "?")
            print(f"→ {cat} ({imp})")
        else:
            error_count += 1
            print("→ ERROR")

        # Save every 20
        if new_count % 20 == 0 and new_count > 0:
            with open(data_file, "w") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

        time.sleep(0.3)

    # Final save
    with open(data_file, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    # Stats
    by_cat = defaultdict(int)
    by_imp = defaultdict(int)
    by_action = defaultdict(int)
    all_tags = defaultdict(int)

    for doc in existing.values():
        a = doc.get("analysis", {})
        by_cat[a.get("categoria", "otro")] += 1
        by_imp[a.get("importancia", "?")] += 1
        by_action[a.get("accion", "?")] += 1
        for tag in a.get("tags", []):
            all_tags[tag.lower()] += 1

    print(f"\n── Resumen ──")
    print(f"  Nuevos: {new_count}  |  Existentes: {skip_count}  |  Errores: {error_count}")
    print(f"  Total analizados: {len(existing)}")

    print(f"\n  Por categoría:")
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {n}")

    print(f"\n  Por importancia:")
    for imp, n in sorted(by_imp.items(), key=lambda x: -x[1]):
        print(f"    {imp}: {n}")

    print(f"\n  Acción recomendada:")
    for act, n in sorted(by_action.items(), key=lambda x: -x[1]):
        print(f"    {act}: {n}")

    print(f"\n  Top tags:")
    for tag, n in sorted(all_tags.items(), key=lambda x: -x[1])[:15]:
        print(f"    #{tag}: {n}")

    print(f"\n  Datos: {data_file}")


# ─── PHASE 3: MAP + PROPOSE ──────────────────────────────────────────────────

MAP_SYSTEM = """Eres un experto en productividad y organización de email. Te doy emails analizados semánticamente.

Genera:

1. **MAPA SEMÁNTICO**: Agrupa los emails por tema REAL (no por remitente). Nombra cada cluster.

2. **ETIQUETAS ÓPTIMAS**: Propón un sistema de etiquetas Gmail basado en el contenido real.
   - Máximo 12 etiquetas
   - Jerárquicas si hace falta (ej: "Negocio/Facturas")
   - Cada etiqueta debe cubrir ≥5 emails

3. **ACCIONES INMEDIATAS**:
   - Emails que requieren respuesta/acción
   - Suscripciones a cancelar (spam disfrazado)
   - Emails importantes sin etiquetar

Responde en markdown."""


PROPOSE_SYSTEM = """Eres un experto en organización de email. Te doy emails analizados semánticamente.

Propón un sistema de etiquetas y asignación CONCRETO en JSON:

{
  "etiquetas": [
    {
      "nombre": "Nombre_Etiqueta",
      "descripcion": "qué emails van aquí",
      "emails": ["msg_id_1", "msg_id_2"],
      "accion": "archivar|mantener"
    }
  ],
  "eliminar": ["msg_id que son spam/basura irrelevante"],
  "importante": ["msg_id que requieren acción del usuario"],
  "cancelar_suscripcion": ["msg_id de newsletters que no aportan valor"]
}

Reglas:
- Máximo 12 etiquetas
- Basadas en CONTENIDO, no en remitente
- Cada email debe tener exactamente 1 etiqueta principal
- "archivar" = quitar del inbox, "mantener" = dejar en inbox
- No crear etiqueta para <5 emails (asignar a la más cercana)"""


def generate_map(account_key: str) -> None:
    data_file = DATA_DIR / f"email_analysis_{account_key}.json"
    map_file = DATA_DIR / f"email_map_{account_key}.md"

    if not data_file.exists():
        print("ERROR: Primero ejecuta --analyze")
        return

    with open(data_file) as f:
        analysis = json.load(f)

    print(f"\n{'='*60}")
    print(f" Mapa semántico Gmail: {len(analysis)} emails")
    print(f"{'='*60}")

    summaries = []
    for msg_id, doc in analysis.items():
        a = doc.get("analysis", {})
        summaries.append(
            f"- ID: {msg_id}\n"
            f"  De: {doc.get('from', '?')}\n"
            f"  Asunto: {doc.get('subject', '?')}\n"
            f"  Fecha: {doc.get('date', '?')}\n"
            f"  Categoría: {a.get('categoria', '?')} | Importancia: {a.get('importancia', '?')}\n"
            f"  Tags: {', '.join(a.get('tags', []))}\n"
            f"  Resumen: {a.get('resumen', '?')}"
        )

    all_text = "\n\n".join(summaries)
    if len(all_text) > 90000:
        all_text = all_text[:90000] + "\n\n[... truncado]"

    print(f"  Enviando a {PROPOSAL_MODEL}...")

    response = call_llm(PROPOSAL_MODEL, MAP_SYSTEM, f"Emails:\n\n{all_text}", max_tokens=5000)

    if response:
        with open(map_file, "w") as f:
            f.write(f"# Mapa Semántico Gmail — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(response)
        print(f"\n{response}")
        print(f"\n  Mapa: {map_file}")
    else:
        print("  ERROR: sin respuesta")


def propose_labels(account_key: str) -> None:
    data_file = DATA_DIR / f"email_analysis_{account_key}.json"
    proposal_file = DATA_DIR / f"email_proposal_{account_key}.json"

    if not data_file.exists():
        print("ERROR: Primero ejecuta --analyze")
        return

    with open(data_file) as f:
        analysis = json.load(f)

    print(f"\n{'='*60}")
    print(f" Propuesta de etiquetas: {len(analysis)} emails")
    print(f"{'='*60}")

    summaries = []
    for msg_id, doc in analysis.items():
        a = doc.get("analysis", {})
        summaries.append(
            f"- ID: {msg_id} | De: {doc.get('from', '?')[:40]}\n"
            f"  Asunto: {doc.get('subject', '?')[:60]}\n"
            f"  Cat: {a.get('categoria', '?')} | Imp: {a.get('importancia', '?')} | Acción: {a.get('accion', '?')}\n"
            f"  Tags: {', '.join(a.get('tags', []))} | Resumen: {a.get('resumen', '?')}"
        )

    all_text = "\n".join(summaries)
    if len(all_text) > 90000:
        all_text = all_text[:90000]

    print(f"  Enviando a {PROPOSAL_MODEL}...")

    response = call_llm(PROPOSAL_MODEL, PROPOSE_SYSTEM, f"Emails:\n\n{all_text}", max_tokens=5000)

    if not response:
        print("  ERROR: sin respuesta")
        return

    try:
        json_match = re.search(r'\{[\s\S]*\}', response)
        proposal = json.loads(json_match.group()) if json_match else {"raw": response}
    except (json.JSONDecodeError, AttributeError):
        proposal = {"raw": response}

    with open(proposal_file, "w") as f:
        json.dump(proposal, f, indent=2, ensure_ascii=False)

    if "etiquetas" in proposal:
        print(f"\n── Etiquetas propuestas ──\n")
        for label in proposal["etiquetas"]:
            nombre = label.get("nombre", "?")
            desc = label.get("descripcion", "")
            emails = label.get("emails", [])
            accion = label.get("accion", "?")
            print(f"  🏷️  {nombre} ({len(emails)} emails, {accion})")
            if desc:
                print(f"     {desc}")

        if proposal.get("eliminar"):
            print(f"\n  🗑️  Eliminar: {len(proposal['eliminar'])} emails")

        if proposal.get("importante"):
            print(f"\n  ⚡ Requieren acción: {len(proposal['importante'])} emails")
            for mid in proposal["importante"][:5]:
                doc = analysis.get(mid, {})
                print(f"     {doc.get('subject', mid)[:60]}")

        if proposal.get("cancelar_suscripcion"):
            print(f"\n  🚫 Cancelar suscripción: {len(proposal['cancelar_suscripcion'])} newsletters")
    else:
        print(response)

    print(f"\n  Propuesta: {proposal_file}")


# ─── PHASE 4: EXECUTE ────────────────────────────────────────────────────────

def execute_labels(account_key: str) -> None:
    data_file = DATA_DIR / f"email_analysis_{account_key}.json"
    proposal_file = DATA_DIR / f"email_proposal_{account_key}.json"

    if not proposal_file.exists():
        print("ERROR: Primero ejecuta --propose")
        return

    with open(proposal_file) as f:
        proposal = json.load(f)

    if "etiquetas" not in proposal:
        print("ERROR: Propuesta sin etiquetas válidas")
        return

    with open(data_file) as f:
        analysis = json.load(f)

    config = ACCOUNTS[account_key]
    total_emails = sum(len(l.get("emails", [])) for l in proposal["etiquetas"])

    print(f"\n{'='*60}")
    print(f" Ejecutar reorganización Gmail: {config['account']}")
    print(f" Etiquetas: {len(proposal['etiquetas'])} | Emails: {total_emails}")
    print(f"{'='*60}")

    confirm = input("\n  ⚠️  Esto etiquetará y archivará emails. ¿Continuar? (s/n): ").strip().lower()
    if confirm != "s":
        print("  Cancelado.")
        return

    service = authenticate(account_key)
    existing_labels = get_labels(service)

    labeled = 0
    archived = 0
    errors = 0

    for label_spec in proposal["etiquetas"]:
        nombre = label_spec.get("nombre", "")
        email_ids = label_spec.get("emails", [])
        accion = label_spec.get("accion", "archivar")

        if not email_ids or not nombre:
            continue

        # Create label if needed
        label_id = existing_labels.get(nombre)
        if not label_id:
            try:
                label_id = create_label(service, nombre)
                existing_labels[nombre] = label_id
                print(f"  + Etiqueta creada: {nombre}")
            except Exception as e:
                print(f"  ✗ Error creando {nombre}: {e}")
                errors += len(email_ids)
                continue

        # Apply label
        add_labels = [label_id]
        remove_labels = ["INBOX"] if accion == "archivar" else []

        try:
            batch_modify(service, email_ids, add_labels=add_labels, remove_labels=remove_labels)
            labeled += len(email_ids)
            if accion == "archivar":
                archived += len(email_ids)
            print(f"  ✓ {nombre}: {len(email_ids)} emails ({accion})")
        except Exception as e:
            errors += len(email_ids)
            print(f"  ✗ {nombre}: {e}")

    # Handle deletions (move to trash)
    to_delete = proposal.get("eliminar", [])
    deleted = 0
    if to_delete:
        confirm_del = input(f"\n  ¿Eliminar {len(to_delete)} emails basura? (s/n): ").strip().lower()
        if confirm_del == "s":
            try:
                batch_modify(service, to_delete, add_labels=["TRASH"], remove_labels=["INBOX"])
                deleted = len(to_delete)
                print(f"  🗑️  {deleted} emails enviados a papelera")
            except Exception as e:
                print(f"  ✗ Error eliminando: {e}")

    print(f"\n── Resumen ──")
    print(f"  Etiquetados:  {labeled}")
    print(f"  Archivados:   {archived}")
    print(f"  Eliminados:   {deleted}")
    print(f"  Errores:      {errors}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente semántico Gmail")
    parser.add_argument("--analyze", action="store_true", help="Fase 1+2: leer y analizar emails")
    parser.add_argument("--map", action="store_true", help="Generar mapa semántico")
    parser.add_argument("--propose", action="store_true", help="Proponer sistema de etiquetas")
    parser.add_argument("--execute", action="store_true", help="Aplicar etiquetas")
    parser.add_argument("--account", choices=["gurufe", "pilates", "all"], default="all")
    parser.add_argument("--query", default="in:inbox", help="Query Gmail (default: in:inbox)")
    parser.add_argument("--todo", action="store_true", help="Analizar TODO el correo (no solo inbox)")
    parser.add_argument("--max", type=int, default=500, help="Máximo de emails a analizar (default: 500)")
    args = parser.parse_args()

    if not any([args.analyze, args.map, args.propose, args.execute]):
        print("Agente semántico Gmail")
        print()
        print("Fases:")
        print("  --analyze            Leer emails y analizar contenido con LLM")
        print("  --map                Generar mapa semántico de clusters")
        print("  --propose            Proponer etiquetas basadas en contenido")
        print("  --execute            Aplicar etiquetas y archivar")
        print()
        print("Opciones:")
        print("  --todo               Analizar todo el correo (no solo inbox)")
        print("  --query 'after:2026/01/01'  Query personalizada")
        print("  --max 1000           Máximo de emails")
        print("  --account gurufe     Solo una cuenta")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    query = "" if args.todo else args.query
    keys = list(ACCOUNTS.keys()) if args.account == "all" else [args.account]

    for key in keys:
        if args.analyze:
            analyze_emails(key, query, args.max)
        if args.map:
            generate_map(key)
        if args.propose:
            propose_labels(key)
        if args.execute:
            execute_labels(key)


if __name__ == "__main__":
    main()
