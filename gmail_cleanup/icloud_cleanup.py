#!/usr/bin/env python3
"""
Agente de limpieza profunda iCloud Drive.
Opera directamente en el filesystem local sincronizado.

Uso:
  python3 icloud_cleanup.py --dry-run    # Ver qué haría sin cambiar nada
  python3 icloud_cleanup.py              # Ejecutar limpieza real
"""

import argparse
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

ICLOUD_ROOT = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
SCRIPT_DIR = Path(__file__).parent


# ─── REGLAS DE LIMPIEZA ──────────────────────────────────────────────────────

# Extensiones de instaladores/basura que se pueden eliminar
INSTALLER_EXTENSIONS = {".dmg", ".exe", ".msi", ".pkg", ".deb", ".rpm"}

# Archivos específicos a eliminar (en la raíz de iCloud)
FILES_TO_DELETE = [
    "Claude Setup.exe",
    "Claude.dmg",
]

# CSVs de importación obsoletos (en raíz) — mover a carpeta de archivo
OBSOLETE_CSV_PATTERNS = [
    "*_import_supabase*.csv",
]

# Carpetas duplicadas OMNI MIND a consolidar
# La estructura correcta es Documents/OMNI-MIND (tiene .git)
# Las demás son copias/versiones antiguas
OMNI_MIND_DUPLICATES = [
    "Documents/OMNI MIND",        # 1 PDF duplicado
    "Documents/OMNI MIND1234",    # PDFs varios, versión antigua
]
OMNI_MIND_CANONICAL = "Documents/OMNI-MIND"

# Descargas: instaladores descargados que sobran
DESCARGAS_TO_CLEAN = [
    "descargas/node-v24.13.1-x64.msi",
    "descargas/node-v25.6.1-x64.msi",
    "descargas/TeamViewer_Setup_x64.exe",
    "descargas/TeamViewer.dmg",
    "descargas/TeamViewerQS.dmg",
]


# ─── ACCIONES ─────────────────────────────────────────────────────────────────

def delete_file(path: Path, dry_run: bool, stats: dict) -> None:
    """Delete a file."""
    size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0
    if dry_run:
        print(f"  [DRY] Eliminar: {path.name} ({size_mb:.1f} MB)")
    else:
        path.unlink()
        print(f"  - Eliminado: {path.name} ({size_mb:.1f} MB)")
    stats["deleted_files"] += 1
    stats["freed_mb"] += size_mb


def move_file(src: Path, dest_dir: Path, dry_run: bool, stats: dict) -> None:
    """Move a file to a directory."""
    if dry_run:
        print(f"  [DRY] Mover: {src.name} → {dest_dir.name}/")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        # Handle name collisions
        if dest.exists():
            stem = src.stem
            suffix = src.suffix
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        shutil.move(str(src), str(dest))
        print(f"  → Movido: {src.name} → {dest_dir.name}/")
    stats["moved_files"] += 1


def delete_directory(path: Path, dry_run: bool, stats: dict) -> None:
    """Delete an empty or consolidated directory."""
    if dry_run:
        count = sum(1 for _ in path.rglob("*") if _.is_file())
        print(f"  [DRY] Eliminar carpeta: {path.name}/ ({count} archivos)")
    else:
        shutil.rmtree(path)
        print(f"  - Carpeta eliminada: {path.name}/")
    stats["deleted_dirs"] += 1


# ─── FASES DE LIMPIEZA ───────────────────────────────────────────────────────

def phase1_delete_installers(dry_run: bool, stats: dict) -> None:
    """Eliminar instaladores y archivos grandes innecesarios."""
    print("\n── Fase 1: Eliminar instaladores y basura ──")

    # Archivos específicos en raíz
    for filename in FILES_TO_DELETE:
        filepath = ICLOUD_ROOT / filename
        if filepath.exists():
            delete_file(filepath, dry_run, stats)

    # Instaladores en descargas/
    for rel_path in DESCARGAS_TO_CLEAN:
        filepath = ICLOUD_ROOT / rel_path
        if filepath.exists():
            delete_file(filepath, dry_run, stats)

    # Buscar otros instaladores sueltos en raíz
    for f in ICLOUD_ROOT.iterdir():
        if f.is_file() and f.suffix.lower() in INSTALLER_EXTENSIONS and f.name not in FILES_TO_DELETE:
            delete_file(f, dry_run, stats)


def phase2_organize_csvs(dry_run: bool, stats: dict) -> None:
    """Mover CSVs de importación Supabase a carpeta de archivo."""
    print("\n── Fase 2: Organizar CSVs de importación ──")

    archive_dir = ICLOUD_ROOT / "STUDIO NUEVO" / "_archivo_importaciones"
    csvs_found = []

    for pattern in OBSOLETE_CSV_PATTERNS:
        csvs_found.extend(ICLOUD_ROOT.glob(pattern))

    # Also check integración shortcuts CSVs
    shortcuts_dir = ICLOUD_ROOT / "integración shortcuts"
    if shortcuts_dir.exists():
        for csv_file in shortcuts_dir.rglob("*.csv"):
            csvs_found.append(csv_file)

    if not csvs_found:
        print("  ~ No se encontraron CSVs de importación sueltos")
        return

    for csv_file in csvs_found:
        move_file(csv_file, archive_dir, dry_run, stats)

    # Move the zip too if it exists
    zip_file = shortcuts_dir / "files.zip"
    if zip_file.exists():
        move_file(zip_file, archive_dir, dry_run, stats)


def phase3_consolidate_omni_mind(dry_run: bool, stats: dict) -> None:
    """Consolidar carpetas duplicadas OMNI MIND."""
    print("\n── Fase 3: Consolidar carpetas OMNI MIND duplicadas ──")

    canonical = ICLOUD_ROOT / OMNI_MIND_CANONICAL
    archive_dir = ICLOUD_ROOT / "Documents" / "_OMNI_MIND_archivo"

    for dup_rel in OMNI_MIND_DUPLICATES:
        dup_path = ICLOUD_ROOT / dup_rel
        if not dup_path.exists():
            continue

        files = list(dup_path.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())

        if dry_run:
            print(f"  [DRY] Mover {dup_path.name}/ ({file_count} archivos) → _OMNI_MIND_archivo/")
        else:
            # Move the entire duplicate folder into archive
            dest = archive_dir / dup_path.name
            archive_dir.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                # Merge: move individual files
                for f in dup_path.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(dup_path)
                        target = dest / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if not target.exists():
                            shutil.move(str(f), str(target))
                shutil.rmtree(dup_path)
            else:
                shutil.move(str(dup_path), str(dest))
            print(f"  → Movido: {dup_path.name}/ → _OMNI_MIND_archivo/")

        stats["moved_files"] += file_count


def phase4_clean_descargas(dry_run: bool, stats: dict) -> None:
    """Limpiar carpeta descargas de archivos ya procesados."""
    print("\n── Fase 4: Limpiar carpeta descargas ──")

    descargas = ICLOUD_ROOT / "descargas"
    if not descargas.exists():
        return

    # Check if descargas/files/ has anything useful
    files_dir = descargas / "files"
    if files_dir.exists():
        contents = list(files_dir.iterdir())
        if not contents:
            if dry_run:
                print("  [DRY] Eliminar carpeta vacía: descargas/files/")
            else:
                files_dir.rmdir()
                print("  - Carpeta vacía eliminada: descargas/files/")

    # Check remaining files in descargas
    remaining = [f for f in descargas.iterdir() if f.is_file() and f.name != ".DS_Store"]
    if remaining:
        print(f"  Archivos restantes en descargas/: {len(remaining)}")
        for f in remaining:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"    {f.name} ({size_mb:.1f} MB)")


def phase5_clean_empty_dirs(dry_run: bool, stats: dict) -> None:
    """Eliminar directorios vacíos y limpiar integración shortcuts si está vacía."""
    print("\n── Fase 5: Limpiar carpetas vacías ──")

    # Check integración shortcuts after CSV move
    shortcuts = ICLOUD_ROOT / "integración shortcuts"
    if shortcuts.exists():
        remaining = list(f for f in shortcuts.rglob("*") if f.is_file() and f.name != ".DS_Store")
        if not remaining:
            delete_directory(shortcuts, dry_run, stats)

    # Find all empty directories
    for dirpath in sorted(ICLOUD_ROOT.rglob("*"), reverse=True):
        if dirpath.is_dir() and dirpath != ICLOUD_ROOT:
            contents = [f for f in dirpath.iterdir() if f.name != ".DS_Store"]
            if not contents:
                if dry_run:
                    print(f"  [DRY] Eliminar carpeta vacía: {dirpath.relative_to(ICLOUD_ROOT)}")
                else:
                    # Remove .DS_Store if present
                    ds_store = dirpath / ".DS_Store"
                    if ds_store.exists():
                        ds_store.unlink()
                    dirpath.rmdir()
                    print(f"  - Carpeta vacía eliminada: {dirpath.relative_to(ICLOUD_ROOT)}")
                stats["deleted_dirs"] += 1


def phase6_report_structure(stats: dict) -> None:
    """Mostrar estructura final de iCloud Drive."""
    print("\n── Estructura final de iCloud Drive ──")

    for item in sorted(ICLOUD_ROOT.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_dir():
            file_count = sum(1 for _ in item.rglob("*") if _.is_file() and _.name != ".DS_Store")
            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) / (1024 * 1024)
            print(f"  📁 {item.name}/ ({file_count} archivos, {size:.1f} MB)")
        elif item.is_symlink():
            target = item.resolve()
            print(f"  🔗 {item.name} → {target}")
        else:
            size = item.stat().st_size / (1024 * 1024)
            print(f"  📄 {item.name} ({size:.1f} MB)")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente de limpieza profunda iCloud Drive")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar qué haría sin cambiar nada")
    args = parser.parse_args()

    if not ICLOUD_ROOT.exists():
        print(f"ERROR: No se encuentra iCloud Drive en {ICLOUD_ROOT}")
        return

    print(f"{'='*60}")
    print(f" Limpieza iCloud Drive")
    print(f" Ruta: {ICLOUD_ROOT}")
    print(f" Modo: {'DRY RUN (sin cambios)' if args.dry_run else 'EJECUCIÓN REAL'}")
    print(f"{'='*60}")

    # Count current state
    total_files = sum(1 for _ in ICLOUD_ROOT.rglob("*") if _.is_file() and _.name != ".DS_Store")
    total_size = sum(f.stat().st_size for f in ICLOUD_ROOT.rglob("*") if f.is_file()) / (1024 * 1024)
    print(f"\nEstado actual: {total_files} archivos, {total_size:.0f} MB")

    stats = {
        "deleted_files": 0,
        "moved_files": 0,
        "deleted_dirs": 0,
        "freed_mb": 0.0,
    }

    phase1_delete_installers(args.dry_run, stats)
    phase2_organize_csvs(args.dry_run, stats)
    phase3_consolidate_omni_mind(args.dry_run, stats)
    phase4_clean_descargas(args.dry_run, stats)
    phase5_clean_empty_dirs(args.dry_run, stats)
    phase6_report_structure(stats)

    print(f"\n── Resumen ──")
    print(f"  Archivos eliminados: {stats['deleted_files']}")
    print(f"  Archivos movidos:    {stats['moved_files']}")
    print(f"  Carpetas eliminadas: {stats['deleted_dirs']}")
    print(f"  Espacio liberado:    {stats['freed_mb']:.1f} MB")

    # Save report
    report = {
        "date": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "stats": stats,
    }
    report_path = SCRIPT_DIR / "icloud_cleanup_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReporte: {report_path}")

    if args.dry_run:
        print("\n⚠️  Esto fue un DRY RUN. Para ejecutar de verdad:")
        print("   python3 icloud_cleanup.py")


if __name__ == "__main__":
    main()
