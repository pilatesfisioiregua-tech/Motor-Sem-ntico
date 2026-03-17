#!/usr/bin/env python3
"""
Agente descargador de facturas/PDFs de Gmail para declaración trimestral.

Uso:
  python3 facturas_downloader.py                          # Trimestre actual
  python3 facturas_downloader.py --trimestre 2026-Q1      # Trimestre específico
  python3 facturas_downloader.py --desde 2026/01/01 --hasta 2026/03/31
  python3 facturas_downloader.py --account pilates         # Solo cuenta pilates
  python3 facturas_downloader.py --todos                   # Todo el historial
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
OUTPUT_BASE = Path.home() / "Facturas"

ACCOUNTS = {
    "gurufe": {
        "account": "gurufe@gmail.com",
        "token_file": "token_facturas_gurufe.json",
    },
    "pilates": {
        "account": "pilatesfisioiregua@gmail.com",
        "token_file": "token_facturas_pilates.json",
    },
}

# Queries para encontrar facturas/recibos con PDFs
FACTURA_QUERIES = [
    # Recibos de servicios tech (los más frecuentes)
    'has:attachment filename:pdf (from:stripe.com OR from:openrouter.ai OR from:anthropic OR from:together)',
    # Facturas explícitas
    'has:attachment filename:pdf (subject:factura OR subject:invoice OR subject:receipt OR subject:recibo)',
    # Proveedores de negocio
    'has:attachment filename:pdf (from:clusterasesores OR from:caixabank OR from:cajarural)',
    # Google / Apple
    'has:attachment filename:pdf (from:google.com subject:factura OR from:google.com subject:invoice)',
    'has:attachment filename:pdf from:apple.com (subject:factura OR subject:invoice OR subject:receipt)',
    # Seguros, bancos, gestoría
    'has:attachment filename:pdf (from:seguro OR from:mapfre OR from:axa OR from:allianz)',
    # Cualquier otro PDF con palabras clave de factura
    'has:attachment filename:pdf (subject:"su factura" OR subject:"your receipt" OR subject:"your invoice")',
]

# Remitentes conocidos → nombre limpio para la carpeta
SENDER_CLEANUP = {
    "openrouter": "OpenRouter",
    "anthropic": "Anthropic",
    "together": "Together_AI",
    "stripe": "Stripe",
    "google": "Google",
    "apple": "Apple",
    "clusterasesores": "Cluster_Asesores",
    "caixabank": "CaixaBank",
    "cajarural": "Caja_Rural",
    "make.com": "Make",
    "mapfre": "Mapfre",
    "wambala": "Wambala",
    "fly.io": "Fly_io",
    "samsung": "Samsung",
    "leroymerlin": "Leroy_Merlin",
    "mediamarkt": "MediaMarkt",
    "amazon": "Amazon",
}


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def authenticate(account_key: str) -> Any:
    """Authenticate with Gmail API (read-only)."""
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


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_quarter_dates(quarter_str: str) -> Tuple[str, str]:
    """Parse '2026-Q1' → ('2026/01/01', '2026/03/31')."""
    match = re.match(r"(\d{4})-Q([1-4])", quarter_str)
    if not match:
        raise ValueError(f"Formato inválido: {quarter_str}. Usa YYYY-Q[1-4]")

    year = int(match.group(1))
    q = int(match.group(2))

    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}

    start_m, start_d = starts[q]
    end_m, end_d = ends[q]

    return f"{year}/{start_m:02d}/{start_d:02d}", f"{year}/{end_m:02d}/{end_d:02d}"


def current_quarter() -> str:
    """Get current quarter string like '2026-Q1'."""
    today = date.today()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


def clean_sender_name(from_header: str) -> str:
    """Extract clean sender name for folder."""
    # Try known senders first
    from_lower = from_header.lower()
    for key, name in SENDER_CLEANUP.items():
        if key in from_lower:
            return name

    # Extract domain name
    match = re.search(r"@([a-zA-Z0-9.-]+)", from_header)
    if match:
        domain = match.group(1)
        # Use first part of domain
        name = domain.split(".")[0].capitalize()
        return name

    # Fallback: use whatever is before <
    match = re.search(r'^"?([^"<]+)', from_header)
    if match:
        return re.sub(r'[^\w\s-]', '', match.group(1).strip()).replace(' ', '_')

    return "Otros"


def clean_filename(filename: str) -> str:
    """Clean filename for filesystem."""
    # Remove problematic characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(cleaned) > 100:
        stem, ext = os.path.splitext(cleaned)
        cleaned = stem[:96] + ext
    return cleaned


# ─── DOWNLOAD ─────────────────────────────────────────────────────────────────

def search_invoices(service: Any, date_from: str, date_to: str) -> List[dict]:
    """Search for all invoice emails in date range. Returns unique messages."""
    seen_ids = set()
    all_messages = []

    for query in FACTURA_QUERIES:
        full_query = f"{query} after:{date_from} before:{date_to}"
        page_token = None

        while True:
            kwargs = {"userId": "me", "q": full_query, "maxResults": 500}
            if page_token:
                kwargs["pageToken"] = page_token

            results = service.users().messages().list(**kwargs).execute()
            messages = results.get("messages", [])

            for msg in messages:
                if msg["id"] not in seen_ids:
                    seen_ids.add(msg["id"])
                    all_messages.append(msg)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

    return all_messages


def download_pdfs_from_message(
    service: Any,
    message_id: str,
    output_dir: Path,
    stats: dict,
) -> List[str]:
    """Download all PDF attachments from a message. Returns list of saved paths."""
    msg = service.users().messages().get(userId="me", id=message_id).execute()

    # Extract metadata
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    from_header = headers.get("From", "unknown")
    subject = headers.get("Subject", "sin_asunto")
    date_str = headers.get("Date", "")
    sender = clean_sender_name(from_header)

    # Parse date for folder organization
    internal_date = int(msg.get("internalDate", 0)) / 1000
    msg_date = datetime.fromtimestamp(internal_date)
    month_folder = msg_date.strftime("%Y-%m")

    # Create output path: Facturas/2026-Q1/2026-01/OpenRouter/
    sender_dir = output_dir / month_folder / sender
    sender_dir.mkdir(parents=True, exist_ok=True)

    saved = []

    def process_parts(parts):
        for part in parts:
            filename = part.get("filename", "")
            if filename.lower().endswith(".pdf"):
                attachment_id = part.get("body", {}).get("attachmentId")
                if attachment_id:
                    # Download attachment
                    att = service.users().messages().attachments().get(
                        userId="me", id=attachment_id, messageId=message_id
                    ).execute()

                    data = base64.urlsafe_b64decode(att["data"])

                    # Clean filename and add date prefix
                    clean_name = clean_filename(filename)
                    date_prefix = msg_date.strftime("%Y%m%d")
                    final_name = f"{date_prefix}_{clean_name}"

                    filepath = sender_dir / final_name

                    # Handle duplicates
                    if filepath.exists():
                        stem, ext = os.path.splitext(final_name)
                        counter = 1
                        while filepath.exists():
                            filepath = sender_dir / f"{stem}_{counter}{ext}"
                            counter += 1

                    with open(filepath, "wb") as f:
                        f.write(data)

                    saved.append(str(filepath))
                    stats["pdfs_downloaded"] += 1
                    stats["total_bytes"] += len(data)

            # Recurse into sub-parts
            if "parts" in part:
                process_parts(part["parts"])

    payload = msg.get("payload", {})
    parts = payload.get("parts", [])

    # Sometimes the attachment is in the body directly
    if not parts and payload.get("filename", "").lower().endswith(".pdf"):
        parts = [payload]

    if parts:
        process_parts(parts)

    return saved


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def process_account(account_key: str, date_from: str, date_to: str, quarter_label: str) -> dict:
    """Process a single account."""
    config = ACCOUNTS[account_key]
    account = config["account"]

    print(f"\n{'='*60}")
    print(f" Descargando facturas: {account}")
    print(f" Periodo: {date_from} → {date_to}")
    print(f"{'='*60}")

    service = authenticate(account_key)

    # Output directory
    output_dir = OUTPUT_BASE / account.split("@")[0] / quarter_label
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "account": account,
        "period": f"{date_from} - {date_to}",
        "quarter": quarter_label,
        "emails_found": 0,
        "pdfs_downloaded": 0,
        "total_bytes": 0,
        "by_sender": defaultdict(int),
        "errors": [],
    }

    # Search
    print(f"\n  Buscando facturas con PDFs...")
    messages = search_invoices(service, date_from, date_to)
    stats["emails_found"] = len(messages)
    print(f"  Encontrados: {len(messages)} emails con PDFs")

    if not messages:
        print("  No se encontraron facturas en este periodo.")
        return stats

    # Download
    print(f"\n  Descargando PDFs...")
    for i, msg in enumerate(messages, 1):
        try:
            saved = download_pdfs_from_message(service, msg["id"], output_dir, stats)
            for path in saved:
                # Track by sender
                sender = Path(path).parent.name
                stats["by_sender"][sender] += 1
                print(f"  [{i}/{len(messages)}] {Path(path).name}")
        except Exception as e:
            stats["errors"].append({"message_id": msg["id"], "error": str(e)})
            print(f"  [{i}/{len(messages)}] ERROR: {e}")

        # Rate limit
        if i % 50 == 0:
            time.sleep(1)

    # Summary
    size_mb = stats["total_bytes"] / (1024 * 1024)
    print(f"\n── Resumen {account} ──")
    print(f"  Emails procesados:  {stats['emails_found']}")
    print(f"  PDFs descargados:   {stats['pdfs_downloaded']}")
    print(f"  Tamaño total:       {size_mb:.1f} MB")
    print(f"  Guardados en:       {output_dir}")
    print(f"\n  Por remitente:")
    for sender, count in sorted(stats["by_sender"].items(), key=lambda x: -x[1]):
        print(f"    {sender}: {count} PDFs")

    if stats["errors"]:
        print(f"\n  Errores: {len(stats['errors'])}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Descargador de facturas/PDFs de Gmail")
    parser.add_argument("--trimestre", help="Trimestre a descargar (ej: 2026-Q1)")
    parser.add_argument("--desde", help="Fecha inicio (YYYY/MM/DD)")
    parser.add_argument("--hasta", help="Fecha fin (YYYY/MM/DD)")
    parser.add_argument("--todos", action="store_true", help="Descargar todo el historial")
    parser.add_argument("--account", choices=["gurufe", "pilates", "all"], default="all")
    args = parser.parse_args()

    # Determine date range
    if args.todos:
        date_from = "2020/01/01"
        date_to = datetime.now().strftime("%Y/%m/%d")
        quarter_label = "historico"
    elif args.desde and args.hasta:
        date_from = args.desde
        date_to = args.hasta
        quarter_label = f"{date_from.replace('/', '')}-{date_to.replace('/', '')}"
    elif args.trimestre:
        date_from, date_to = get_quarter_dates(args.trimestre)
        quarter_label = args.trimestre
    else:
        # Default: trimestre actual
        q = current_quarter()
        date_from, date_to = get_quarter_dates(q)
        quarter_label = q
        print(f"Trimestre por defecto: {q}")

    # Process accounts
    if args.account == "all":
        keys = list(ACCOUNTS.keys())
    else:
        keys = [args.account]

    all_stats = []
    for key in keys:
        stats = process_account(key, date_from, date_to, quarter_label)
        # Convert defaultdict for JSON
        stats["by_sender"] = dict(stats["by_sender"])
        all_stats.append(stats)

    # Save report
    report_path = OUTPUT_BASE / f"facturas_report_{quarter_label}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({"date": datetime.now().isoformat(), "accounts": all_stats}, f, indent=2, ensure_ascii=False)
    print(f"\nReporte: {report_path}")


if __name__ == "__main__":
    main()
