"""Universal knowledge ingestion — index any folder into knowledge_base.

Safe by default: NEVER deletes existing data. Uses MD5 dedup to skip unchanged files.
The tsvector trigger (trg_kb_tsv) auto-populates full-text search on INSERT.

Usage:
    python3 ingest.py /path/to/folder --scope repo
    python3 ingest.py /path/to/docs --scope external:pilates --mode full

Modes:
    incremental (default): skip files whose MD5 hash hasn't changed
    full: delete entries matching scope prefix, then re-insert all
"""

import os
import re
import sys
import json
import hashlib
import argparse
from datetime import datetime, timezone
from typing import Optional


# ── Config ────────────────────────────────────────────────────────────────

MAX_CHUNK = 3000          # chars per chunk
MAX_FILE_READ = 80_000    # max chars to read per file
BATCH_SIZE = 200          # rows per INSERT batch

INDEXABLE_EXTENSIONS = {
    ".md", ".py", ".sql", ".json", ".yaml", ".yml", ".toml",
    ".sh", ".html", ".ts", ".js", ".jsx", ".tsx", ".css",
    ".txt", ".rst", ".csv", ".xml", ".cfg", ".ini", ".env",
    ".dockerfile", ".gitignore", ".editorconfig",
}

# Files without extension that we want to index
INDEXABLE_NAMES = {
    "Dockerfile", "Makefile", "Procfile", "fly.toml",
    "CLAUDE.md", "README.md", "LICENSE",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build",
    ".DS_Store", ".tox", ".eggs", "*.egg-info",
    ".cache", ".ruff_cache",
}

# Patterns in filenames to skip (secrets, binaries)
SKIP_PATTERNS = [
    r'\.pyc$', r'\.pyo$', r'\.so$', r'\.o$', r'\.class$',
    r'\.jar$', r'\.png$', r'\.jpg$', r'\.jpeg$', r'\.gif$',
    r'\.ico$', r'\.svg$', r'\.woff', r'\.ttf$', r'\.eot$',
    r'\.zip$', r'\.tar', r'\.gz$', r'\.bz2$', r'\.xz$',
    r'\.pdf$', r'\.doc', r'\.xls', r'\.ppt',
    r'\.mp[34]$', r'\.wav$', r'\.avi$', r'\.mov$',
    r'\.db$', r'\.sqlite', r'\.lock$',
    r'package-lock\.json$', r'yarn\.lock$',
]

# Lines in .env files that contain secrets
SECRET_PATTERNS = [
    r'(?i)(key|secret|password|token|credential|auth).*=',
]


# ── Connection ────────────────────────────────────────────────────────────

def _get_conn():
    import psycopg2
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        # Fallback for local dev with fly proxy
        url = "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"
    conn = psycopg2.connect(url, connect_timeout=15)
    conn.autocommit = False
    return conn


# ── File type detection ───────────────────────────────────────────────────

def _detect_tipo(ext: str, fname: str) -> str:
    if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".sh"):
        return "code"
    if ext in (".md", ".rst", ".txt"):
        return "documentation"
    if ext == ".sql":
        return "schema"
    if ext == ".csv":
        return "data"
    if ext in (".html", ".css"):
        return "frontend"
    if fname.lower() in ("dockerfile", "procfile", "makefile"):
        return "devops"
    return "config"


def _should_skip_file(fname: str, fpath: str) -> bool:
    for pat in SKIP_PATTERNS:
        if re.search(pat, fname, re.IGNORECASE):
            return True
    # Skip files >MAX_FILE_READ
    try:
        if os.path.getsize(fpath) > MAX_FILE_READ * 2:
            return True
    except OSError:
        return True
    return False


# ── Chunking ──────────────────────────────────────────────────────────────

def _chunk_markdown(content: str, filepath: str) -> list:
    """Split markdown by ## headers."""
    chunks = []
    sections = re.split(r'^(#{1,3}\s+.+)$', content, flags=re.MULTILINE)

    current_section = os.path.basename(filepath)
    current_text = ""

    for part in sections:
        if re.match(r'^#{1,3}\s+', part):
            if current_text.strip():
                chunks.append({
                    "seccion": current_section,
                    "texto": current_text.strip()[:MAX_CHUNK],
                })
            current_section = part.strip().lstrip("#").strip()
            current_text = part + "\n"
        else:
            current_text += part

    if current_text.strip():
        chunks.append({
            "seccion": current_section,
            "texto": current_text.strip()[:MAX_CHUNK],
        })

    return chunks if chunks else [{"seccion": "", "texto": content[:MAX_CHUNK]}]


def _chunk_python(content: str, filepath: str) -> list:
    """Split Python by class/def definitions."""
    chunks = []
    parts = re.split(r'^((?:class|def)\s+\w+)', content, flags=re.MULTILINE)

    current_name = os.path.basename(filepath)
    current_text = ""

    for part in parts:
        if re.match(r'^(?:class|def)\s+\w+', part):
            if current_text.strip():
                chunks.append({
                    "seccion": current_name,
                    "texto": current_text.strip()[:MAX_CHUNK],
                })
            current_name = part.strip()
            current_text = part
        else:
            current_text += part

    if current_text.strip():
        chunks.append({
            "seccion": current_name,
            "texto": current_text.strip()[:MAX_CHUNK],
        })

    return chunks if chunks else [{"seccion": "", "texto": content[:MAX_CHUNK]}]


def _chunk_sql(content: str, filepath: str) -> list:
    """Split SQL by major statements."""
    chunks = []
    statements = re.split(
        r'^((?:CREATE|ALTER|INSERT|UPDATE|DELETE|DROP|GRANT)\s)',
        content, flags=re.MULTILINE | re.IGNORECASE
    )

    current_text = ""
    for part in statements:
        if re.match(r'^(?:CREATE|ALTER|INSERT|UPDATE|DELETE|DROP|GRANT)\s', part, re.IGNORECASE):
            if current_text.strip():
                chunks.append({
                    "seccion": current_text.strip()[:80],
                    "texto": current_text.strip()[:MAX_CHUNK],
                })
            current_text = part
        else:
            current_text += part

    if current_text.strip():
        chunks.append({
            "seccion": current_text.strip()[:80],
            "texto": current_text.strip()[:MAX_CHUNK],
        })

    return chunks if chunks else [{"seccion": "", "texto": content[:MAX_CHUNK]}]


def _chunk_default(content: str, filepath: str) -> list:
    """Default chunking: split into MAX_CHUNK pieces with overlap."""
    if len(content) <= MAX_CHUNK:
        return [{"seccion": "", "texto": content}]

    chunks = []
    overlap = 200
    pos = 0
    idx = 0
    while pos < len(content):
        end = min(pos + MAX_CHUNK, len(content))
        chunk_text = content[pos:end]
        chunks.append({
            "seccion": f"chunk_{idx}",
            "texto": chunk_text,
        })
        idx += 1
        pos = end - overlap if end < len(content) else end

    return chunks


def _chunk_file(content: str, filepath: str, ext: str) -> list:
    """Route to appropriate chunker."""
    if ext == ".md":
        return _chunk_markdown(content, filepath)
    if ext == ".py":
        return _chunk_python(content, filepath)
    if ext == ".sql":
        return _chunk_sql(content, filepath)
    return _chunk_default(content, filepath)


def _sanitize_env_content(content: str) -> str:
    """Remove secret values from .env files, keep structure."""
    lines = []
    for line in content.splitlines():
        for pat in SECRET_PATTERNS:
            if re.search(pat, line):
                key = line.split("=", 1)[0] if "=" in line else line
                line = f"{key}=***REDACTED***"
                break
        lines.append(line)
    return "\n".join(lines)


# ── Core ingestion ────────────────────────────────────────────────────────

def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()


def ingest_folder(folder_path: str, scope_prefix: str = "repo",
                  mode: str = "incremental", conn=None,
                  embed: bool = True) -> dict:
    """Ingest all files in folder_path into knowledge_base.

    Args:
        folder_path: Absolute path to folder to ingest
        scope_prefix: Scope prefix (e.g. "repo", "external:pilates")
        mode: "incremental" (skip unchanged) or "full" (delete scope + reinsert)
        conn: Optional DB connection (creates one if not provided)

    Returns:
        dict with stats: files, chunks, skipped, unchanged, errors
    """
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()

    stats = {
        "files": 0, "chunks": 0, "skipped": 0,
        "unchanged": 0, "errors": 0, "scope": scope_prefix,
    }

    try:
        cur = conn.cursor()

        # In full mode, delete existing entries for this scope
        if mode == "full":
            cur.execute(
                "DELETE FROM knowledge_base WHERE scope LIKE %s",
                [f"{scope_prefix}/%"]
            )
            deleted = cur.rowcount
            conn.commit()
            print(f"  [full mode] Deleted {deleted} entries with scope '{scope_prefix}/%'")

        # Load existing hashes for incremental mode
        existing_hashes = {}
        if mode == "incremental":
            cur.execute("""
                SELECT documento, metadata->>'file_hash' as hash
                FROM knowledge_base
                WHERE scope LIKE %s AND metadata->>'file_hash' IS NOT NULL
            """, [f"{scope_prefix}/%"])
            for row in cur.fetchall():
                if row[0] and row[1]:
                    existing_hashes[row[0]] = row[1]

        # Walk the folder
        batch = []
        now = datetime.now(timezone.utc).isoformat()

        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()

                # Check if indexable
                indexable = ext in INDEXABLE_EXTENSIONS or fname in INDEXABLE_NAMES
                if not indexable or _should_skip_file(fname, fpath):
                    stats["skipped"] += 1
                    continue

                # Read file
                try:
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read(MAX_FILE_READ)
                except OSError:
                    stats["errors"] += 1
                    continue

                if not content.strip():
                    stats["skipped"] += 1
                    continue

                rel_path = os.path.relpath(fpath, folder_path)

                # Sanitize .env files
                if ext == ".env" or fname.startswith(".env"):
                    content = _sanitize_env_content(content)

                # Incremental: check hash
                file_hash = _md5(content)
                if mode == "incremental" and rel_path in existing_hashes:
                    if existing_hashes[rel_path] == file_hash:
                        stats["unchanged"] += 1
                        continue
                    # Hash changed — delete old entries for this file, then re-insert
                    cur.execute(
                        "DELETE FROM knowledge_base WHERE scope LIKE %s AND documento = %s",
                        [f"{scope_prefix}/%", rel_path]
                    )

                # Detect type and chunk
                tipo = _detect_tipo(ext, fname)
                scope = f"{scope_prefix}/{tipo}"
                chunks = _chunk_file(content, fpath, ext)
                file_size = len(content)

                for i, chunk in enumerate(chunks):
                    meta = json.dumps({
                        "file_hash": file_hash,
                        "file_ext": ext or os.path.basename(fname),
                        "file_size": file_size,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "ingested_at": now,
                    })
                    batch.append((
                        scope, tipo, "L2",
                        chunk["texto"], rel_path,
                        chunk.get("seccion", ""),
                        meta,
                    ))
                    stats["chunks"] += 1

                stats["files"] += 1

                # Flush batch + COMMIT incrementally (avoid giant transaction)
                if len(batch) >= BATCH_SIZE:
                    try:
                        _flush_batch(cur, batch, embed=embed)
                        conn.commit()
                    except Exception as e:
                        stats["errors"] += 1
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    batch = []

                # Progress
                if stats["files"] % 200 == 0:
                    print(f"  ... {stats['files']} files, {stats['chunks']} chunks")

        # Final flush
        if batch:
            try:
                _flush_batch(cur, batch, embed=embed)
                conn.commit()
            except Exception as e:
                stats["errors"] += 1
                try:
                    conn.rollback()
                except Exception:
                    pass

        return stats

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        stats["errors"] += 1
        stats["error_detail"] = str(e)
        return stats
    finally:
        if own_conn:
            conn.close()


def _generate_embeddings_for_batch(texts: list) -> list:
    """Generate embeddings for a batch of texts. Returns list of embedding vectors or Nones."""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from core.embedder import get_embedder
        embedder = get_embedder()
        results = embedder.embed_batch(texts)
        return results
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Embedding generation failed during ingest: {e}")
        return [None] * len(texts)


def _flush_batch(cur, batch: list, embed: bool = True) -> None:
    """Insert a batch of rows into knowledge_base, optionally with embeddings."""
    from psycopg2.extras import execute_values

    if embed:
        texts = [row[3] for row in batch]  # texto is at index 3
        embeddings = _generate_embeddings_for_batch(texts)
        # Augment batch with embedding column
        augmented = []
        for row, emb in zip(batch, embeddings):
            emb_str = str(emb) if emb else None
            augmented.append(row + (emb_str,))
        execute_values(
            cur,
            """INSERT INTO knowledge_base
               (scope, tipo, nivel, texto, documento, seccion, metadata, embedding)
               VALUES %s""",
            augmented,
            template="(%s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)",
            page_size=BATCH_SIZE,
        )
    else:
        execute_values(
            cur,
            """INSERT INTO knowledge_base
               (scope, tipo, nivel, texto, documento, seccion, metadata)
               VALUES %s""",
            batch,
            template="(%s, %s, %s, %s, %s, %s, %s::jsonb)",
            page_size=BATCH_SIZE,
        )


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest folder into knowledge_base")
    parser.add_argument("folder", help="Path to folder to ingest")
    parser.add_argument("--scope", default="repo", help="Scope prefix (default: repo)")
    parser.add_argument("--mode", choices=["incremental", "full"], default="incremental",
                        help="Ingestion mode (default: incremental)")
    parser.add_argument("--no-embed", action="store_true",
                        help="Skip embedding generation (text-only ingest)")
    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"ERROR: Not a directory: {folder}")
        sys.exit(1)

    print(f"Ingesting: {folder}")
    print(f"  scope: {args.scope}")
    print(f"  mode: {args.mode}")
    print()

    stats = ingest_folder(folder, scope_prefix=args.scope, mode=args.mode,
                           embed=not args.no_embed)

    print()
    print(f"=== Ingestion complete ===")
    print(f"  Files processed: {stats['files']}")
    print(f"  Chunks created:  {stats['chunks']}")
    print(f"  Skipped (type):  {stats['skipped']}")
    print(f"  Unchanged (hash): {stats['unchanged']}")
    print(f"  Errors:          {stats['errors']}")
    if stats.get("error_detail"):
        print(f"  Error detail:    {stats['error_detail']}")


if __name__ == "__main__":
    main()
