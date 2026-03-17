#!/usr/bin/env python3
"""
Agente de limpieza profunda Gmail — soporta múltiples cuentas.
Uso:
  python gmail_cleanup.py --dry-run          # Ver qué haría sin cambiar nada
  python gmail_cleanup.py                    # Ejecutar limpieza real
  python gmail_cleanup.py --account gurufe   # Solo una cuenta
  python gmail_cleanup.py --account pilates  # Solo cuenta pilates
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import ACCOUNTS, GURUFE_CONFIG, PILATES_CONFIG

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def authenticate(account_config: dict) -> Any:
    """Authenticate with Gmail API using OAuth2. Returns a Gmail service."""
    token_path = SCRIPT_DIR / account_config["token_file"]
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: No se encuentra {CREDENTIALS_FILE}")
                print("Descárgalo de Google Cloud Console > APIs & Services > Credentials")
                sys.exit(1)
            print(f"\n🔐 Autenticando {account_config['account']}...")
            print("Se abrirá el navegador. Selecciona la cuenta correcta.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── LABEL HELPERS ────────────────────────────────────────────────────────────

def get_labels(service: Any) -> Dict[str, str]:
    """Returns {label_name: label_id}."""
    results = service.users().labels().list(userId="me").execute()
    return {l["name"]: l["id"] for l in results.get("labels", [])}


def create_label(service: Any, name: str, dry_run: bool) -> Optional[str]:
    """Create a label. Returns label ID."""
    if dry_run:
        print(f"  [DRY] Crearía etiqueta: {name}")
        return None
    body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    result = service.users().labels().create(userId="me", body=body).execute()
    print(f"  + Etiqueta creada: {name} (ID: {result['id']})")
    return result["id"]


def delete_label(service: Any, label_id: str, label_name: str, dry_run: bool) -> None:
    """Delete a label."""
    if dry_run:
        print(f"  [DRY] Eliminaría etiqueta: {label_name}")
        return
    service.users().labels().delete(userId="me", id=label_id).execute()
    print(f"  - Etiqueta eliminada: {label_name}")


# ─── MESSAGE HELPERS ──────────────────────────────────────────────────────────

def search_messages(service: Any, query: str, max_results: int = 500) -> List[dict]:
    """Search for messages matching query. Returns list of {id, threadId}."""
    messages = []
    page_token = None

    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": min(max_results - len(messages), 500)}
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.users().messages().list(**kwargs).execute()
        batch = results.get("messages", [])
        messages.extend(batch)

        if len(messages) >= max_results:
            break
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return messages[:max_results]


def batch_modify_messages(
    service: Any,
    message_ids: List[str],
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    dry_run: bool = False,
) -> int:
    """Batch modify messages. Returns count of modified messages."""
    if not message_ids:
        return 0
    if dry_run:
        return len(message_ids)

    # Gmail API limits batch to 1000 messages
    total = 0
    for i in range(0, len(message_ids), 1000):
        chunk = message_ids[i : i + 1000]
        body = {"ids": chunk}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        service.users().messages().batchModify(userId="me", body=body).execute()
        total += len(chunk)
        if i + 1000 < len(message_ids):
            time.sleep(0.5)  # Rate limit courtesy

    return total


# ─── MERGE LABELS ─────────────────────────────────────────────────────────────

def merge_labels(
    service: Any,
    from_name: str,
    to_name: str,
    labels: Dict[str, str],
    dry_run: bool,
) -> int:
    """Move all messages from one label to another, then delete the source label."""
    from_id = labels.get(from_name)
    to_id = labels.get(to_name)

    if not from_id:
        print(f"  ! Etiqueta origen no encontrada: {from_name}")
        return 0

    # Find messages with the source label
    msgs = search_messages(service, f"label:{from_name.replace(' ', '-')}")
    if not msgs:
        print(f"  ~ {from_name} está vacía, eliminando...")
        delete_label(service, from_id, from_name, dry_run)
        return 0

    msg_ids = [m["id"] for m in msgs]

    if dry_run:
        print(f"  [DRY] Movería {len(msg_ids)} emails de {from_name} → {to_name}")
        return len(msg_ids)

    # Add destination label, remove source label
    add = [to_id] if to_id else []
    batch_modify_messages(service, msg_ids, add_labels=add, remove_labels=[from_id])
    delete_label(service, from_id, from_name, dry_run=False)
    print(f"  ✓ Consolidado {len(msg_ids)} emails: {from_name} → {to_name}")
    return len(msg_ids)


# ─── CREATE FILTERS ──────────────────────────────────────────────────────────

def create_filter(
    service: Any,
    query: str,
    label_id: str,
    archive: bool,
    dry_run: bool,
) -> None:
    """Create a Gmail filter for future messages."""
    if dry_run:
        print(f"  [DRY] Crearía filtro: {query[:60]}...")
        return

    body = {
        "criteria": {"query": query},
        "action": {"addLabelIds": [label_id]},
    }
    if archive:
        body["action"]["removeLabelIds"] = ["INBOX"]

    try:
        service.users().settings().filters().create(userId="me", body=body).execute()
        print(f"  + Filtro creado: {query[:60]}...")
    except Exception as e:
        print(f"  ! Error creando filtro: {e}")


# ─── MAIN PROCESS ────────────────────────────────────────────────────────────

def process_account(account_config: dict, dry_run: bool) -> dict:
    """Process a single Gmail account. Returns stats."""
    account = account_config["account"]
    print(f"\n{'='*60}")
    print(f" Procesando: {account}")
    print(f" Modo: {'DRY RUN (sin cambios)' if dry_run else 'EJECUCIÓN REAL'}")
    print(f"{'='*60}")

    service = authenticate(account_config)
    labels = get_labels(service)

    stats = {
        "account": account,
        "labels_deleted": 0,
        "labels_created": 0,
        "labels_merged": 0,
        "messages_classified": 0,
        "messages_archived": 0,
        "filters_created": 0,
        "rules_detail": [],
    }

    # ── Paso 1: Eliminar etiquetas obsoletas ──
    print(f"\n── Paso 1: Eliminar etiquetas obsoletas ──")
    for label_name in account_config["labels_to_delete"]:
        label_id = labels.get(label_name)
        if label_id:
            delete_label(service, label_id, label_name, dry_run)
            stats["labels_deleted"] += 1
        else:
            print(f"  ~ No encontrada (ya eliminada?): {label_name}")

    # ── Paso 2: Consolidar etiquetas ──
    print(f"\n── Paso 2: Consolidar etiquetas ──")
    for merge in account_config["labels_to_merge"]:
        count = merge_labels(service, merge["from"], merge["to"], labels, dry_run)
        stats["labels_merged"] += count

    # Refresh labels after deletions/merges
    if not dry_run:
        labels = get_labels(service)

    # ── Paso 3: Crear etiquetas nuevas ──
    print(f"\n── Paso 3: Crear etiquetas nuevas ──")
    for label_name in account_config["labels_to_create"]:
        if label_name in labels:
            print(f"  ~ Ya existe: {label_name}")
        else:
            new_id = create_label(service, label_name, dry_run)
            if new_id:
                labels[label_name] = new_id
            stats["labels_created"] += 1

    # ── Paso 4: Clasificar emails ──
    print(f"\n── Paso 4: Clasificar emails por reglas ──")
    for rule in account_config["rules"]:
        name = rule["name"]
        query = rule["query"]
        label_name = rule["label"]
        action = rule["action"]

        # Only process inbox messages
        full_query = f"in:inbox ({query})"
        msgs = search_messages(service, full_query)
        msg_ids = [m["id"] for m in msgs]

        if not msg_ids:
            continue

        label_id = labels.get(label_name)
        add_labels = [label_id] if label_id else []
        remove_labels = ["INBOX"] if action == "archive" else []

        if action == "trash":
            remove_labels = []
            add_labels = ["TRASH"]

        prefix = "[DRY] " if dry_run else ""
        print(f"  {prefix}{name}: {len(msg_ids)} emails → {label_name} ({action})")

        if not dry_run and msg_ids:
            batch_modify_messages(service, msg_ids, add_labels=add_labels, remove_labels=remove_labels)

        stats["messages_classified"] += len(msg_ids)
        if action == "archive":
            stats["messages_archived"] += len(msg_ids)
        stats["rules_detail"].append({"name": name, "count": len(msg_ids), "label": label_name, "action": action})

    # ── Paso 5: Crear filtros para el futuro ──
    print(f"\n── Paso 5: Crear filtros automáticos ──")
    for filter_config in account_config.get("filters_to_create", []):
        label_id = labels.get(filter_config["label"])
        if not label_id:
            print(f"  ! Etiqueta no encontrada para filtro: {filter_config['label']}")
            continue
        create_filter(
            service,
            filter_config["query"],
            label_id,
            filter_config.get("archive", False),
            dry_run,
        )
        stats["filters_created"] += 1

    # ── Resumen ──
    print(f"\n── Resumen {account} ──")
    print(f"  Etiquetas eliminadas: {stats['labels_deleted']}")
    print(f"  Etiquetas creadas:    {stats['labels_created']}")
    print(f"  Emails consolidados:  {stats['labels_merged']}")
    print(f"  Emails clasificados:  {stats['messages_classified']}")
    print(f"  Emails archivados:    {stats['messages_archived']}")
    print(f"  Filtros creados:      {stats['filters_created']}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Agente de limpieza profunda Gmail")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar qué haría sin cambiar nada")
    parser.add_argument("--account", choices=["gurufe", "pilates", "all"], default="all", help="Cuenta a procesar")
    args = parser.parse_args()

    if args.account == "gurufe":
        configs = [GURUFE_CONFIG]
    elif args.account == "pilates":
        configs = [PILATES_CONFIG]
    else:
        configs = ACCOUNTS

    all_stats = []
    for config in configs:
        stats = process_account(config, args.dry_run)
        all_stats.append(stats)

    # Save report
    report_path = SCRIPT_DIR / "cleanup_report.json"
    with open(report_path, "w") as f:
        json.dump({"dry_run": args.dry_run, "accounts": all_stats}, f, indent=2, ensure_ascii=False)
    print(f"\nReporte guardado en: {report_path}")

    if args.dry_run:
        print("\n⚠️  Esto fue un DRY RUN. Para ejecutar de verdad:")
        print("   python gmail_cleanup.py")


if __name__ == "__main__":
    main()
