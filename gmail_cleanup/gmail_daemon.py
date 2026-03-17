#!/usr/bin/env python3
"""
Daemon de clasificación semántica Gmail en tiempo real.
Cada 5 minutos detecta emails nuevos, los lee con LLM y los clasifica.

Uso:
  python3 gmail_daemon.py                    # Ejecutar en primer plano
  python3 gmail_daemon.py --interval 300     # Cada 5 min (default)
  python3 gmail_daemon.py --interval 60      # Cada 1 min
  python3 gmail_daemon.py --account gurufe   # Solo una cuenta
  python3 gmail_daemon.py --install          # Instalar como servicio macOS
  python3 gmail_daemon.py --uninstall        # Desinstalar servicio
  python3 gmail_daemon.py --status           # Ver estado del servicio
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
STATE_DIR = SCRIPT_DIR / "daemon_state"
LOG_DIR = SCRIPT_DIR / "logs"

OPENROUTER_KEY = "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"
ANALYSIS_MODEL = "deepseek/deepseek-chat-v3-0324"

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

# Etiquetas que el daemon puede asignar
# El LLM elige una de estas basándose en el contenido
LABEL_CATEGORIES = {
    "Facturas":           {"accion": "archivar", "desc": "facturas, recibos, pagos"},
    "Newsletters":        {"accion": "archivar", "desc": "marketing, promos, suscripciones"},
    "Tech":               {"accion": "archivar", "desc": "servicios dev, APIs, cloud"},
    "Trabajo":            {"accion": "mantener", "desc": "negocio, pilates studio, clientes"},
    "Personal":           {"accion": "mantener", "desc": "comunicación personal directa"},
    "Bancos":             {"accion": "mantener", "desc": "bancos, finanzas, seguros"},
    "Seguridad":          {"accion": "mantener", "desc": "alertas seguridad, 2FA, contraseñas"},
    "Viaje":              {"accion": "mantener", "desc": "reservas, vuelos, hoteles"},
    "Formacion":          {"accion": "archivar", "desc": "cursos, coaching, desarrollo personal"},
    "Notificaciones":     {"accion": "archivar", "desc": "notificaciones automáticas de apps"},
    "Spam_Comercial":     {"accion": "archivar", "desc": "spam comercial, ofertas no deseadas"},
}

PLIST_NAME = "com.omnimind.gmail-daemon"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"


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
                log(f"ERROR: No se encuentra {CREDENTIALS_FILE}")
                sys.exit(1)
            log(f"Autenticando {config['account']}... (se abrirá el navegador)")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── LOGGING ──────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    """Log to stdout and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"daemon_{datetime.now().strftime('%Y-%m')}.log"
    with open(log_file, "a") as f:
        f.write(line + "\n")


# ─── GMAIL HELPERS ────────────────────────────────────────────────────────────

def get_history_id(account_key: str) -> Optional[str]:
    """Get last processed history ID."""
    state_file = STATE_DIR / f"history_{account_key}.json"
    if state_file.exists():
        with open(state_file) as f:
            data = json.load(f)
            return data.get("historyId")
    return None


def save_history_id(account_key: str, history_id: str) -> None:
    """Save last processed history ID."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"history_{account_key}.json"
    with open(state_file, "w") as f:
        json.dump({"historyId": history_id, "updated": datetime.now().isoformat()}, f)


def get_new_messages(service: Any, account_key: str) -> List[str]:
    """Get message IDs received since last check."""
    history_id = get_history_id(account_key)

    if not history_id:
        # First run: get current history ID and process recent inbox
        profile = service.users().getProfile(userId="me").execute()
        save_history_id(account_key, profile["historyId"])

        # Process last 20 unread inbox messages as initial batch
        results = service.users().messages().list(
            userId="me", q="in:inbox is:unread", maxResults=20
        ).execute()
        return [m["id"] for m in results.get("messages", [])]

    # Get history since last check
    try:
        history = service.users().history().list(
            userId="me",
            startHistoryId=history_id,
            historyTypes=["messageAdded"],
            labelId="INBOX",
        ).execute()
    except Exception as e:
        if "404" in str(e) or "historyId" in str(e).lower():
            # History expired, reset
            profile = service.users().getProfile(userId="me").execute()
            save_history_id(account_key, profile["historyId"])
            return []
        raise

    # Update history ID
    new_history_id = history.get("historyId", history_id)
    save_history_id(account_key, new_history_id)

    # Extract new message IDs
    msg_ids = set()
    for record in history.get("history", []):
        for msg_added in record.get("messagesAdded", []):
            msg = msg_added.get("message", {})
            labels = msg.get("labelIds", [])
            if "INBOX" in labels:
                msg_ids.add(msg["id"])

    return list(msg_ids)


def get_message_content(service: Any, message_id: str) -> Optional[dict]:
    """Get message with headers and body."""
    try:
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    except Exception:
        return None

    headers = {}
    for h in msg.get("payload", {}).get("headers", []):
        headers[h["name"]] = h["value"]

    body = extract_body(msg.get("payload", {}))

    return {
        "id": message_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "labels": msg.get("labelIds", []),
        "snippet": msg.get("snippet", ""),
        "body": body[:2000] if body else "",
    }


def extract_body(payload: dict) -> str:
    parts = _flatten_parts(payload)
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                except Exception:
                    pass
    for part in parts:
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    return re.sub(r'<[^>]+>', ' ', html)
                except Exception:
                    pass
    data = payload.get("body", {}).get("data", "")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""


def _flatten_parts(payload: dict) -> List[dict]:
    parts = []
    if "parts" in payload:
        for part in payload["parts"]:
            parts.extend(_flatten_parts(part))
    else:
        parts.append(payload)
    return parts


def get_or_create_label(service: Any, name: str, label_cache: dict) -> Optional[str]:
    """Get label ID, create if needed."""
    if name in label_cache:
        return label_cache[name]

    # Check existing
    results = service.users().labels().list(userId="me").execute()
    for l in results.get("labels", []):
        label_cache[l["name"]] = l["id"]

    if name in label_cache:
        return label_cache[name]

    # Create
    try:
        body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        result = service.users().labels().create(userId="me", body=body).execute()
        label_cache[name] = result["id"]
        log(f"  + Etiqueta creada: {name}")
        return result["id"]
    except Exception as e:
        log(f"  ! Error creando etiqueta {name}: {e}")
        return None


# ─── LLM CLASSIFICATION ──────────────────────────────────────────────────────

CLASSIFY_SYSTEM = """Clasifica este email en UNA de estas categorías. Responde SOLO con el JSON.

Categorías disponibles:
{categories}

Responde SOLO en JSON:
{{"categoria": "NombreExacto", "confianza": "alta|media|baja", "razon": "por qué"}}"""


def classify_email(msg: dict) -> Optional[dict]:
    """Classify a single email using LLM."""
    categories_text = "\n".join(
        f"- {name}: {info['desc']}" for name, info in LABEL_CATEGORIES.items()
    )

    system = CLASSIFY_SYSTEM.replace("{categories}", categories_text)

    body_preview = msg["body"][:1500] if msg["body"] else msg["snippet"]
    user_msg = (
        f"De: {msg['from']}\n"
        f"Asunto: {msg['subject']}\n"
        f"Contenido:\n{body_preview}"
    )

    payload = json.dumps({
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 150,
        "temperature": 0.1,
    })

    try:
        result = subprocess.run(
            ["curl", "-s", "https://openrouter.ai/api/v1/chat/completions",
             "-H", "Content-Type: application/json",
             "-H", f"Authorization: Bearer {OPENROUTER_KEY}",
             "-d", payload],
            capture_output=True, text=True, timeout=30,
        )

        data = json.loads(result.stdout)
        content = data["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass

    return None


# ─── MAIN LOOP ────────────────────────────────────────────────────────────────

def process_account(account_key: str) -> dict:
    """Check for new emails and classify them."""
    config = ACCOUNTS[account_key]
    service = authenticate(account_key)
    label_cache = {}

    stats = {"checked": 0, "classified": 0, "archived": 0, "errors": 0}

    # Get new messages
    new_ids = get_new_messages(service, account_key)
    if not new_ids:
        return stats

    log(f"  {config['account']}: {len(new_ids)} emails nuevos")

    for msg_id in new_ids:
        msg = get_message_content(service, msg_id)
        if not msg:
            stats["errors"] += 1
            continue

        stats["checked"] += 1
        subject = (msg["subject"] or "sin asunto")[:50]

        # Skip if already has a user label (already classified)
        user_labels = [l for l in msg["labels"] if l.startswith("Label_")]
        if user_labels:
            continue

        # Classify with LLM
        classification = classify_email(msg)
        if not classification:
            log(f"    ? {subject} → error LLM")
            stats["errors"] += 1
            continue

        category = classification.get("categoria", "")
        confidence = classification.get("confianza", "baja")

        # Validate category exists
        if category not in LABEL_CATEGORIES:
            # Fuzzy match
            for name in LABEL_CATEGORIES:
                if name.lower() in category.lower() or category.lower() in name.lower():
                    category = name
                    break
            else:
                log(f"    ? {subject} → categoría desconocida: {category}")
                stats["errors"] += 1
                continue

        # Apply label
        label_id = get_or_create_label(service, category, label_cache)
        if not label_id:
            stats["errors"] += 1
            continue

        action = LABEL_CATEGORIES[category]["accion"]
        add_labels = [label_id]
        remove_labels = ["INBOX"] if action == "archivar" else []

        # Only auto-archive if high/medium confidence
        if confidence == "baja":
            remove_labels = []  # Don't archive low confidence

        try:
            body = {"ids": [msg_id]}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels
            service.users().messages().batchModify(userId="me", body=body).execute()

            action_str = "archivado" if remove_labels else "etiquetado"
            log(f"    ✓ {subject} → {category} ({confidence}, {action_str})")
            stats["classified"] += 1
            if remove_labels:
                stats["archived"] += 1
        except Exception as e:
            log(f"    ✗ {subject}: {e}")
            stats["errors"] += 1

        time.sleep(0.3)

    return stats


def run_daemon(account_keys: List[str], interval: int) -> None:
    """Main daemon loop."""
    log(f"Daemon iniciado. Cuentas: {', '.join(account_keys)}. Intervalo: {interval}s")
    log(f"Categorías: {', '.join(LABEL_CATEGORIES.keys())}")

    cycle = 0
    while True:
        cycle += 1
        total_stats = {"checked": 0, "classified": 0, "archived": 0, "errors": 0}

        for key in account_keys:
            try:
                stats = process_account(key)
                for k in total_stats:
                    total_stats[k] += stats[k]
            except Exception as e:
                log(f"  ERROR {key}: {e}")

        if total_stats["checked"] > 0:
            log(f"  Ciclo #{cycle}: {total_stats['checked']} revisados, "
                f"{total_stats['classified']} clasificados, "
                f"{total_stats['archived']} archivados, "
                f"{total_stats['errors']} errores")

        time.sleep(interval)


# ─── INSTALL/UNINSTALL macOS SERVICE ──────────────────────────────────────────

def install_service(account_keys: List[str], interval: int) -> None:
    """Install as macOS launchd service."""
    python_path = sys.executable
    script_path = Path(__file__).resolve()
    accounts_arg = ",".join(account_keys)

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--account-keys</string>
        <string>{accounts_arg}</string>
        <string>--interval</string>
        <string>{interval}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{SCRIPT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_DIR}/daemon_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR}/daemon_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:{Path.home()}/Library/Python/3.9/bin</string>
    </dict>
</dict>
</plist>"""

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(PLIST_PATH, "w") as f:
        f.write(plist_content)

    # Load the service
    subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
    print(f"Servicio instalado: {PLIST_NAME}")
    print(f"  Plist: {PLIST_PATH}")
    print(f"  Logs:  {LOG_DIR}/daemon_stdout.log")
    print(f"  Intervalo: cada {interval}s")
    print(f"  Cuentas: {', '.join(account_keys)}")
    print(f"\nEl daemon arrancará automáticamente al iniciar sesión.")
    print(f"Para ver logs en tiempo real:")
    print(f"  tail -f {LOG_DIR}/daemon_stdout.log")


def uninstall_service() -> None:
    """Uninstall macOS launchd service."""
    if PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
        PLIST_PATH.unlink()
        print(f"Servicio desinstalado: {PLIST_NAME}")
    else:
        print("Servicio no encontrado.")


def check_status() -> None:
    """Check service status."""
    result = subprocess.run(
        ["launchctl", "list", PLIST_NAME],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Servicio ACTIVO: {PLIST_NAME}")
        print(result.stdout)

        # Show recent logs
        log_file = LOG_DIR / "daemon_stdout.log"
        if log_file.exists():
            print("\nÚltimas líneas del log:")
            subprocess.run(["tail", "-20", str(log_file)])
    else:
        print(f"Servicio NO activo: {PLIST_NAME}")
        if PLIST_PATH.exists():
            print(f"  Plist existe en: {PLIST_PATH}")
            print(f"  Intenta: launchctl load {PLIST_PATH}")
        else:
            print(f"  No instalado. Usa: python3 gmail_daemon.py --install")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Daemon de clasificación semántica Gmail")
    parser.add_argument("--interval", type=int, default=300, help="Segundos entre checks (default: 300 = 5min)")
    parser.add_argument("--account", choices=["gurufe", "pilates", "all"], default="all")
    parser.add_argument("--account-keys", help="Comma-separated account keys (internal)")
    parser.add_argument("--install", action="store_true", help="Instalar como servicio macOS")
    parser.add_argument("--uninstall", action="store_true", help="Desinstalar servicio")
    parser.add_argument("--status", action="store_true", help="Ver estado del servicio")
    args = parser.parse_args()

    if args.status:
        check_status()
        return

    if args.uninstall:
        uninstall_service()
        return

    # Resolve account keys
    if args.account_keys:
        keys = args.account_keys.split(",")
    elif args.account == "all":
        keys = list(ACCOUNTS.keys())
    else:
        keys = [args.account]

    if args.install:
        install_service(keys, args.interval)
        return

    # Run daemon
    run_daemon(keys, args.interval)


if __name__ == "__main__":
    main()
