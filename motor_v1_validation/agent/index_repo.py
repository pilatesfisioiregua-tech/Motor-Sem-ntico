"""Index repository files into knowledge_base for semantic search."""

import os
import json
import re
import sys

# Extensions to index
INDEXABLE_EXTENSIONS = {
    ".md", ".py", ".sql", ".json", ".yaml", ".yml", ".toml",
    ".sh", ".html", ".ts", ".js",
}

# Directories to skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".DS_Store",
}

# Max chunk size (chars)
MAX_CHUNK = 3000


def _get_conn():
    import psycopg2
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise ValueError("DATABASE_URL not set")
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = False
    return conn


def _detect_tipo(ext: str) -> str:
    """Determine tipo from file extension."""
    if ext in (".py", ".js", ".ts", ".sh"):
        return "code"
    if ext in (".md", ".rst", ".txt"):
        return "documentation"
    if ext == ".sql":
        return "schema"
    return "config"


def _chunk_markdown(content: str, filepath: str) -> list:
    """Split markdown by ## headers into chunks."""
    chunks = []
    sections = re.split(r'^(#{1,3}\s+.+)$', content, flags=re.MULTILINE)

    current_section = os.path.basename(filepath)
    current_text = ""

    for part in sections:
        if re.match(r'^#{1,3}\s+', part):
            # Save previous chunk
            if current_text.strip():
                chunks.append({
                    "seccion": current_section,
                    "texto": current_text.strip()[:MAX_CHUNK],
                })
            current_section = part.strip().lstrip("#").strip()
            current_text = part + "\n"
        else:
            current_text += part

    # Last chunk
    if current_text.strip():
        chunks.append({
            "seccion": current_section,
            "texto": current_text.strip()[:MAX_CHUNK],
        })

    return chunks if chunks else [{"seccion": "", "texto": content[:MAX_CHUNK]}]


def _chunk_python(content: str, filepath: str) -> list:
    """Split Python by function/class definitions."""
    chunks = []
    # Split by def/class at top level
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


def _chunk_file(content: str, filepath: str, ext: str) -> list:
    """Chunk a file based on its type."""
    if ext == ".md":
        return _chunk_markdown(content, filepath)
    if ext == ".py":
        return _chunk_python(content, filepath)
    # Default: single chunk
    return [{"seccion": "", "texto": content[:MAX_CHUNK]}]


def index_repo(repo_dir: str) -> dict:
    """Index all files in repo_dir into knowledge_base."""
    conn = _get_conn()
    stats = {"files": 0, "chunks": 0, "errors": 0, "skipped": 0}

    try:
        # Collect all current repo documents to detect stale entries
        seen_docs = set()

        # Walk the repo
        for root, dirs, files in os.walk(repo_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in INDEXABLE_EXTENSIONS:
                    stats["skipped"] += 1
                    continue

                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, repo_dir)
                seen_docs.add(rel_path)

                try:
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read(50000)  # Max 50K per file
                except OSError:
                    stats["errors"] += 1
                    continue

                if not content.strip():
                    stats["skipped"] += 1
                    continue

                tipo = _detect_tipo(ext)
                chunks = _chunk_file(content, fpath, ext)

                with conn.cursor() as cur:
                    # Remove old chunks for this specific file (incremental, not full wipe)
                    cur.execute(
                        "DELETE FROM knowledge_base WHERE scope = 'repo' AND documento = %s",
                        [rel_path]
                    )
                    for chunk in chunks:
                        cur.execute("""
                            INSERT INTO knowledge_base
                                (scope, tipo, nivel, texto, documento, seccion)
                            VALUES ('repo', %s, 'L2', %s, %s, %s)
                        """, [
                            tipo,
                            chunk["texto"],
                            rel_path,
                            chunk["seccion"],
                        ])
                        stats["chunks"] += 1

                stats["files"] += 1

        # Remove entries for deleted files (no longer in repo)
        if seen_docs:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM knowledge_base
                    WHERE scope = 'repo' AND documento IS NOT NULL
                      AND documento NOT IN %s
                """, [tuple(seen_docs)])
                stale = cur.rowcount
                if stale:
                    print(f"  Removed {stale} stale entries from deleted files")

        conn.commit()
        print(f"  Indexed {stats['files']} files, {stats['chunks']} chunks")
        return stats

    except Exception as e:
        conn.rollback()
        print(f"  ERROR indexing repo: {e}")
        stats["errors"] += 1
        return stats
    finally:
        conn.close()


if __name__ == "__main__":
    repo_dir = os.environ.get("CODE_OS_PROJECT_DIR", "/repo")
    if len(sys.argv) > 1:
        repo_dir = sys.argv[1]

    print(f"Indexing repo: {repo_dir}")
    result = index_repo(repo_dir)
    print(f"Result: {json.dumps(result, indent=2)}")
