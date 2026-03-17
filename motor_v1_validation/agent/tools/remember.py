"""Remember tool — search project knowledge (DB or local context/ or web)."""

import os
import json
import glob as globmod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import ToolRegistry


def _search_knowledge_base(query: str, limit: int = 10, session_id: str = None,
                           scope: str = None) -> Optional[str]:
    """Search knowledge_base via hybrid search (FTS + Hebbian) with ILIKE fallback."""
    try:
        from core.neural_db import get_neural_db
        ndb = get_neural_db()
        results = ndb.semantic_search(query, limit=limit, scope=scope, session_id=session_id)
        if results:
            for r in results:
                if r.get("texto") and len(r["texto"]) > 500:
                    r["texto"] = r["texto"][:500] + "..."
                # Include search scores for transparency
                r["_search"] = {
                    "fts_rank": round(r.pop("fts_rank", 0), 3),
                    "hebbian_boost": round(r.pop("hebbian_boost", 0), 3),
                    "combined_score": round(r.pop("combined_score", 0), 3),
                }
            return json.dumps(results, indent=2, default=str)
    except Exception:
        pass
    return None


def _search_context_dir(query: str, project_dir: str) -> Optional[str]:
    """Search local context/ directory for matching files."""
    context_dir = os.path.join(project_dir, "context")
    if not os.path.isdir(context_dir):
        # Try parent dirs
        for parent in [os.path.dirname(project_dir), os.path.dirname(os.path.dirname(project_dir))]:
            candidate = os.path.join(parent, "context")
            if os.path.isdir(candidate):
                context_dir = candidate
                break
        else:
            return None

    results = []
    query_lower = query.lower()

    for fpath in sorted(globmod.glob(os.path.join(context_dir, "**"), recursive=True)):
        if not os.path.isfile(fpath):
            continue
        fname = os.path.basename(fpath).lower()
        # Match by filename first
        name_match = query_lower in fname

        try:
            with open(fpath, "r", errors="replace") as f:
                content = f.read(5000)
        except OSError:
            continue

        content_match = query_lower in content.lower()

        if name_match or content_match:
            # Extract relevant snippet
            if content_match and not name_match:
                idx = content.lower().find(query_lower)
                start = max(0, idx - 200)
                end = min(len(content), idx + len(query) + 200)
                snippet = content[start:end]
            else:
                snippet = content[:500]

            results.append({
                "file": os.path.relpath(fpath, context_dir),
                "snippet": snippet.strip(),
                "match": "filename" if name_match else "content",
            })

        if len(results) >= 10:
            break

    return json.dumps(results, indent=2, ensure_ascii=False) if results else None


def _search_web(query: str, max_results: int = 3) -> Optional[str]:
    """Search the web via DuckDuckGo as last-resort fallback."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return None
        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "snippet": r.get("body", r.get("snippet", "")),
            })
        return json.dumps(formatted, indent=2, ensure_ascii=False)
    except ImportError:
        return None
    except Exception:
        return None


_CURRENT_SESSION_ID = None

def set_session_id(session_id: str) -> None:
    """Set current session ID for Hebbian learning."""
    global _CURRENT_SESSION_ID
    _CURRENT_SESSION_ID = session_id


def tool_remember(query: str, source: str = "auto", scope: str = None) -> str:
    """Search project knowledge. Cascade: DB → context/ files → web.

    Args:
        query: What to search for.
        source: "db", "files", "web", or "auto" (cascade all).
        scope: Optional scope filter (e.g. "patrones", "chief", "repo").
    """
    results = []

    if source in ("auto", "db"):
        db_result = _search_knowledge_base(query, session_id=_CURRENT_SESSION_ID, scope=scope)
        if db_result:
            results.append(f"=== knowledge_base (DB) ===\n{db_result}")

    if source in ("auto", "files") and not results:
        project_dir = os.environ.get("CODE_OS_PROJECT_DIR", os.getcwd())
        files_result = _search_context_dir(query, project_dir)
        if files_result:
            results.append(f"=== context/ (files) ===\n{files_result}")

    if source in ("auto", "web") and not results:
        web_result = _search_web(query)
        if web_result:
            results.append(f"=== web search ===\n{web_result}")

    if not results:
        return f"No results found for '{query}'. Try a different query or check that knowledge_base table / context/ directory exists."

    return "\n\n".join(results)


def tool_remember_save(title: str, content: str, category: str = "general") -> str:
    """Save a piece of knowledge to the knowledge_base table."""
    try:
        from .database import _get_conn
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO knowledge_base (scope, tipo, texto)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, ["chief", category, f"# {title}\n\n{content}"])
                row = cur.fetchone()
            conn.commit()
            return json.dumps({"status": "OK", "id": row[0]}, default=str)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def _tool_ingest_folder(path: str, scope: str = "imported", mode: str = "incremental") -> str:
    """Ingest a folder into knowledge_base."""
    # Resolve @project/ prefix
    if path.startswith("@project/") or path == "@project":
        project_dir = os.environ.get("CODE_OS_PROJECT_DIR", os.getcwd())
        clean = path[len("@project/"):] if path.startswith("@project/") else ""
        path = os.path.join(project_dir, clean) if clean else project_dir

    if not os.path.isdir(path):
        return f"ERROR: Not a directory: {path}"

    try:
        from ingest import ingest_folder
        stats = ingest_folder(path, scope_prefix=scope, mode=mode)
        return json.dumps(stats, indent=2, default=str)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("remember", {
        "name": "remember",
        "description": "Search project knowledge with hybrid search (full-text + Hebbian learning). Queries knowledge_base (14K entries) and/or local context/ files. Learns from co-access patterns to improve over time.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for (keywords, concepts, topics)"},
            "source": {"type": "string", "enum": ["auto", "db", "files", "web"],
                       "description": "Where to search. 'auto' cascades: DB → files → web. Default: auto"},
            "scope": {"type": "string", "description": "Filter by scope: 'patrones' (technical patterns), 'chief' (architecture/decisions), 'repo' (code). Omit for all scopes."},
        }, "required": ["query"]}
    }, lambda a: tool_remember(a["query"], a.get("source", "auto"), a.get("scope")), category="knowledge")

    registry.register("remember_save", {
        "name": "remember_save",
        "description": "Save a piece of knowledge to the database for future recall. Use after important decisions, discoveries, or when the user says 'remember this'.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Short title for the knowledge entry"},
            "content": {"type": "string", "description": "Full content to save"},
            "category": {"type": "string", "description": "Category: general, decision, experiment, architecture, bug. Default: general"},
        }, "required": ["title", "content"]}
    }, lambda a: tool_remember_save(a["title"], a["content"], a.get("category", "general")),
    category="knowledge")

    registry.register("ingest_folder", {
        "name": "ingest_folder",
        "description": "Ingest a folder into the knowledge base for future search. Safe: uses hash dedup, never deletes unless mode=full. Use @project/ prefix for project folders.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Folder path. Use @project/docs/ for project subfolders."},
            "scope": {"type": "string", "description": "Scope prefix for entries (e.g. 'external:pilates', 'docs:maestro'). Default: 'imported'"},
            "mode": {"type": "string", "enum": ["incremental", "full"],
                     "description": "incremental=skip unchanged files, full=delete scope+reindex. Default: incremental"},
        }, "required": ["path"]}
    }, lambda a: _tool_ingest_folder(a["path"], a.get("scope", "imported"), a.get("mode", "incremental")),
    category="knowledge")
