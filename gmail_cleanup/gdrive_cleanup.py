#!/usr/bin/env python3
"""
Agente de limpieza profunda Google Drive.
Usa Google Drive API v3 para organizar archivos en ambas cuentas.

Uso:
  python3 gdrive_cleanup.py --dry-run                    # Ver qué haría
  python3 gdrive_cleanup.py --dry-run --account gurufe   # Solo gurufe
  python3 gdrive_cleanup.py                              # Ejecutar real
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"


# ─── CONFIGURACIÓN POR CUENTA ────────────────────────────────────────────────

ACCOUNTS = {
    "gurufe": {
        "account": "gurufe@gmail.com",
        "token_file": "token_drive_gurufe.json",
    },
    "pilates": {
        "account": "pilatesfisioiregua@gmail.com",
        "token_file": "token_drive_pilates.json",
    },
}

# Carpetas de organización a crear si no existen
FOLDERS_TO_CREATE = [
    "Instaladores",        # .dmg, .exe, .msi, .pkg
    "Documentos",          # .pdf, .docx, .xlsx, .pages
    "Imágenes",            # .jpg, .png, .heic, .gif
    "Videos",              # .mp4, .mov, .avi
    "Audio",               # .m4a, .mp3, .wav
    "Archivos",            # .zip, .tar, .gz
    "Datos",               # .csv, .json, .xml
    "Código",              # .py, .js, .md (dev files)
]

# Mapeo extensión → carpeta destino
EXTENSION_MAP = {
    # Instaladores
    ".dmg": "Instaladores", ".exe": "Instaladores", ".msi": "Instaladores",
    ".pkg": "Instaladores", ".deb": "Instaladores", ".rpm": "Instaladores",
    # Documentos
    ".pdf": "Documentos", ".docx": "Documentos", ".doc": "Documentos",
    ".xlsx": "Documentos", ".xls": "Documentos", ".pptx": "Documentos",
    ".pages": "Documentos", ".numbers": "Documentos", ".keynote": "Documentos",
    ".txt": "Documentos",
    # Imágenes
    ".jpg": "Imágenes", ".jpeg": "Imágenes", ".png": "Imágenes",
    ".gif": "Imágenes", ".heic": "Imágenes", ".heif": "Imágenes",
    ".webp": "Imágenes", ".svg": "Imágenes", ".jfif": "Imágenes",
    # Video
    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos",
    ".mkv": "Videos", ".webm": "Videos",
    # Audio
    ".m4a": "Audio", ".mp3": "Audio", ".wav": "Audio",
    ".aac": "Audio", ".flac": "Audio",
    # Archivos comprimidos
    ".zip": "Archivos", ".tar": "Archivos", ".gz": "Archivos",
    ".rar": "Archivos", ".7z": "Archivos",
    # Datos
    ".csv": "Datos", ".json": "Datos", ".xml": "Datos",
    # Código
    ".py": "Código", ".js": "Código", ".ts": "Código",
    ".md": "Código", ".yaml": "Código", ".yml": "Código",
    ".html": "Código", ".css": "Código",
}


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def authenticate(account_key: str) -> Any:
    """Authenticate with Google Drive API. Returns Drive service."""
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
                print("Descárgalo de Google Cloud Console > APIs & Services > Credentials")
                sys.exit(1)
            print(f"\n🔐 Autenticando {config['account']} (Drive)...")
            print("Se abrirá el navegador. Selecciona la cuenta correcta.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ─── DRIVE HELPERS ────────────────────────────────────────────────────────────

def list_all_files(service: Any, query: str = None, fields: str = "files(id, name, mimeType, parents, size, modifiedTime)") -> List[dict]:
    """List all files matching query. Handles pagination."""
    all_files = []
    page_token = None

    while True:
        kwargs = {
            "pageSize": 1000,
            "fields": f"nextPageToken, {fields}",
            "spaces": "drive",
        }
        if query:
            kwargs["q"] = query
        if page_token:
            kwargs["pageToken"] = page_token

        results = service.files().list(**kwargs).execute()
        all_files.extend(results.get("files", []))

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return all_files


def get_or_create_folder(service: Any, name: str, parent_id: str = None, dry_run: bool = False) -> Optional[str]:
    """Get existing folder ID or create it. Returns folder ID."""
    # Search for existing folder
    query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)", spaces="drive").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    if dry_run:
        print(f"  [DRY] Crearía carpeta: {name}")
        return None

    # Create folder
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  + Carpeta creada: {name}")
    return folder["id"]


def move_file(service: Any, file_id: str, file_name: str, dest_folder_id: str, current_parents: List[str], dry_run: bool) -> bool:
    """Move a file to a different folder."""
    if dry_run:
        return True

    previous_parents = ",".join(current_parents)
    service.files().update(
        fileId=file_id,
        addParents=dest_folder_id,
        removeParents=previous_parents,
        fields="id, parents",
    ).execute()
    return True


def delete_file(service: Any, file_id: str, file_name: str, dry_run: bool) -> bool:
    """Move file to trash."""
    if dry_run:
        return True
    service.files().update(fileId=file_id, body={"trashed": True}).execute()
    return True


# ─── ANÁLISIS ─────────────────────────────────────────────────────────────────

def analyze_drive(service: Any) -> dict:
    """Analyze the drive contents and return a report."""
    print("\n  Analizando contenido del Drive...")

    # Get all files (not trashed)
    all_files = list_all_files(service, query="trashed = false")

    # Separate folders and files
    folders = [f for f in all_files if f["mimeType"] == "application/vnd.google-apps.folder"]
    files = [f for f in all_files if f["mimeType"] != "application/vnd.google-apps.folder"]

    # Count by type
    by_extension = defaultdict(list)
    root_files = []
    total_size = 0

    # Get root folder ID
    root_query = "'root' in parents and trashed = false"
    root_items = list_all_files(service, query=root_query)

    for f in files:
        name = f.get("name", "")
        ext = os.path.splitext(name)[1].lower()
        size = int(f.get("size", 0))
        total_size += size
        by_extension[ext].append(f)

        # Check if in root
        parents = f.get("parents", [])
        # We'll collect root files separately below

    # Files in root (no parent folder, or parent is root)
    root_files_list = [f for f in root_items if f["mimeType"] != "application/vnd.google-apps.folder"]

    report = {
        "total_files": len(files),
        "total_folders": len(folders),
        "total_size_mb": total_size / (1024 * 1024),
        "root_files": len(root_files_list),
        "by_extension": {ext: len(flist) for ext, flist in sorted(by_extension.items(), key=lambda x: -len(x[1]))},
        "top_extensions": [(ext, len(flist)) for ext, flist in sorted(by_extension.items(), key=lambda x: -len(x[1]))[:15]],
    }

    return report


# ─── LIMPIEZA ─────────────────────────────────────────────────────────────────

def organize_root_files(service: Any, dry_run: bool, stats: dict) -> None:
    """Move files in root to appropriate folders based on extension."""
    print("\n── Organizar archivos sueltos en raíz ──")

    # Get files in root
    root_files = list_all_files(
        service,
        query="'root' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'",
    )

    if not root_files:
        print("  ~ No hay archivos sueltos en la raíz")
        return

    # Create destination folders
    folder_ids = {}
    needed_folders = set()
    for f in root_files:
        ext = os.path.splitext(f.get("name", ""))[1].lower()
        dest = EXTENSION_MAP.get(ext)
        if dest:
            needed_folders.add(dest)

    for folder_name in needed_folders:
        folder_id = get_or_create_folder(service, folder_name, dry_run=dry_run)
        if folder_id:
            folder_ids[folder_name] = folder_id

    # Move files
    for f in root_files:
        name = f.get("name", "")
        ext = os.path.splitext(name)[1].lower()
        dest_folder = EXTENSION_MAP.get(ext)

        if not dest_folder:
            continue  # Skip files we don't know how to categorize

        dest_id = folder_ids.get(dest_folder)
        parents = f.get("parents", [])
        size_mb = int(f.get("size", 0)) / (1024 * 1024)

        prefix = "[DRY] " if dry_run else ""
        print(f"  {prefix}{name} ({size_mb:.1f} MB) → {dest_folder}/")

        if dest_id:
            move_file(service, f["id"], name, dest_id, parents, dry_run)

        stats["moved_files"] += 1


def find_duplicates(service: Any, dry_run: bool, stats: dict) -> None:
    """Find and report duplicate files (same name + same size)."""
    print("\n── Buscar archivos duplicados ──")

    all_files = list_all_files(
        service,
        query="trashed = false and mimeType != 'application/vnd.google-apps.folder'",
    )

    # Group by (name, size)
    groups = defaultdict(list)
    for f in all_files:
        key = (f.get("name", ""), f.get("size", "0"))
        groups[key].append(f)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    if not duplicates:
        print("  ~ No se encontraron duplicados")
        return

    print(f"  Encontrados {len(duplicates)} grupos de duplicados:")
    for (name, size), files in sorted(duplicates.items()):
        size_mb = int(size) / (1024 * 1024)
        print(f"    {name} ({size_mb:.1f} MB) × {len(files)} copias")
        stats["duplicates_found"] += len(files) - 1

    # Don't auto-delete duplicates — just report them
    print(f"\n  ⚠️  Total duplicados: {stats['duplicates_found']} (no se eliminan automáticamente)")


def clean_trash(service: Any, dry_run: bool, stats: dict) -> None:
    """Report trash status."""
    print("\n── Estado de la papelera ──")

    trashed = list_all_files(service, query="trashed = true")
    if trashed:
        total_size = sum(int(f.get("size", 0)) for f in trashed) / (1024 * 1024)
        print(f"  {len(trashed)} archivos en papelera ({total_size:.1f} MB)")
        if not dry_run:
            print("  Para vaciar la papelera manualmente: Drive > Papelera > Vaciar papelera")
    else:
        print("  ~ Papelera vacía")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def process_account(account_key: str, dry_run: bool) -> dict:
    """Process a single Google Drive account."""
    config = ACCOUNTS[account_key]
    account = config["account"]

    print(f"\n{'='*60}")
    print(f" Google Drive: {account}")
    print(f" Modo: {'DRY RUN' if dry_run else 'EJECUCIÓN REAL'}")
    print(f"{'='*60}")

    service = authenticate(account_key)

    stats = {
        "account": account,
        "moved_files": 0,
        "deleted_files": 0,
        "duplicates_found": 0,
        "folders_created": 0,
    }

    # Analyze
    report = analyze_drive(service)
    print(f"\n  Total: {report['total_files']} archivos, {report['total_folders']} carpetas, {report['total_size_mb']:.0f} MB")
    print(f"  Archivos en raíz: {report['root_files']}")
    print(f"  Top tipos: {', '.join(f'{ext}({n})' for ext, n in report['top_extensions'][:8])}")

    # Organize
    organize_root_files(service, dry_run, stats)
    find_duplicates(service, dry_run, stats)
    clean_trash(service, dry_run, stats)

    print(f"\n── Resumen {account} ──")
    print(f"  Archivos movidos:     {stats['moved_files']}")
    print(f"  Duplicados detectados: {stats['duplicates_found']}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Agente de limpieza profunda Google Drive")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar qué haría sin cambiar nada")
    parser.add_argument("--account", choices=["gurufe", "pilates", "all"], default="all", help="Cuenta a procesar")
    args = parser.parse_args()

    if args.account == "all":
        keys = list(ACCOUNTS.keys())
    else:
        keys = [args.account]

    all_stats = []
    for key in keys:
        stats = process_account(key, args.dry_run)
        all_stats.append(stats)

    # Save report
    report_path = SCRIPT_DIR / "gdrive_cleanup_report.json"
    with open(report_path, "w") as f:
        json.dump({"dry_run": args.dry_run, "date": datetime.now().isoformat(), "accounts": all_stats}, f, indent=2, ensure_ascii=False)
    print(f"\nReporte: {report_path}")

    if args.dry_run:
        print("\n⚠️  DRY RUN. Para ejecutar de verdad:")
        print("   python3 gdrive_cleanup.py")


if __name__ == "__main__":
    main()
