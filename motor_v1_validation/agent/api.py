"""Code OS v3 — FastAPI wrapper for Omni Mind integration.

Endpoints:
  POST /code-os/execute  → SSE stream execution (CEO interface)
  GET  /code-os/health   → Proactive health check
  GET  /code-os/status   → System status (version, models, tools)
  GET  /code-os/session/{id} → Get session status/result
  GET  /code-os/sessions → List recent sessions
  GET  /chat → Web chat interface
  POST /chat/send → Send message, receive SSE stream
  GET  /ceo → CEO Dashboard with Code OS tab
  GET  /health → Health check
"""

import os
import sys
import json
import uuid
import asyncio
from typing import Optional
from dataclasses import dataclass

# Ensure agent/ is in path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

from core.api import _load_env
from core import VERSION
from persistence import SupabaseClient
from chat import ChatEngine

_load_env()

app = FastAPI(
    title="Code OS v2 API",
    description="El Enjambre — An open source Claude Code with 55+ tools",
    version=VERSION,
)

# Mount static files for chat UI
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# In-memory session tracking (supplement to Supabase)
_running_sessions = {}  # session_id -> {"status": "running"|"completed"|"failed", "result": dict}

# Chat engine (lazy init)
_chat_engine: Optional[ChatEngine] = None


def _get_chat_engine() -> ChatEngine:
    global _chat_engine
    if _chat_engine is None:
        _chat_engine = ChatEngine(
            project_dir=os.environ.get(
                "CODE_OS_PROJECT_DIR",
                "/repo" if os.path.isdir("/repo") else "/Users/jesusfernandezdominguez/omni-mind-cerebro",
            ),
            strategy=os.environ.get("CODE_OS_STRATEGY", "tiered"),
            forced_model=os.environ.get("CODE_OS_MODEL"),
            max_cost=float(os.environ.get("CODE_OS_MAX_COST", "15.0")),
        )
    return _chat_engine


class ChatRequest(BaseModel):
    chat_id: str
    message: str
    project: Optional[str] = None
    force_phase: Optional[str] = None  # "design" | "done" — force phase transition


class ExecuteRequest(BaseModel):
    mode: str = "goal"  # "goal", "vision", "briefing"
    goal: Optional[str] = None
    vision: Optional[str] = None
    briefing_path: Optional[str] = None
    project: str = "."
    strategy: str = "tiered"
    model: Optional[str] = None
    max_iter: int = 30
    budget: float = 2.0
    autonomous: bool = True
    swarm: bool = False


class CEOExecuteRequest(BaseModel):
    input: str
    mode: str = "auto"  # "auto", "goal", "briefing"
    project_dir: Optional[str] = None
    file_content: Optional[str] = None
    file_name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str


def _run_code_os_sync(session_id: str, request: ExecuteRequest):
    """Run Code OS synchronously (called in background thread)."""
    try:
        from code_os import run_code_os

        goal = request.goal or request.vision or f"Execute: {request.briefing_path}"

        result = run_code_os(
            goal=goal,
            mode=request.mode,
            project_dir=os.path.abspath(request.project),
            strategy=request.strategy,
            forced_model=request.model,
            max_iterations=request.max_iter,
            max_cost=request.budget,
            verbose=True,
            vision_text=request.vision if request.mode == "vision" else None,
            briefing_path=request.briefing_path if request.mode == "briefing" else None,
            autonomous=request.autonomous,
            swarm=request.swarm,
        )

        _running_sessions[session_id] = {
            "status": "completed" if result.get("stop_reason") == "DONE" else "failed",
            "result": result,
        }
    except Exception as e:
        _running_sessions[session_id] = {
            "status": "failed",
            "result": {"error": str(e)},
        }


@app.post("/code-os/execute")
async def execute_sse(request: CEOExecuteRequest):
    """Execute Code OS with SSE streaming — CEO interface endpoint."""
    import time as _time
    import threading

    from core.intent import translate_intent
    from core.reporter import Reporter

    user_input = request.input
    project_dir = request.project_dir or os.environ.get(
        "CODE_OS_PROJECT_DIR",
        "/repo" if os.path.isdir("/repo") else ".",
    )

    # Detect briefing from attached file
    file_is_briefing = False
    if request.file_content and request.file_name:
        if request.file_name.endswith('.md') and '# BRIEFING:' in request.file_content[:500]:
            file_is_briefing = True

    # Translate business language to technical goal
    intent = translate_intent(user_input, {})
    mode = request.mode
    if mode == "auto":
        if file_is_briefing:
            mode = "briefing"
        else:
            mode = "goal"

    # Inject file content as context for non-briefing files
    if request.file_content and not file_is_briefing:
        goal = intent["technical_goal"] + f"\n\n--- Archivo adjunto: {request.file_name} ---\n{request.file_content}"
    else:
        goal = intent["technical_goal"]

    def event_stream():
        import queue as _queue

        session_id = str(uuid.uuid4())
        start = _time.time()

        # Emit intent translation
        if intent["category"]:
            yield f"data: {json.dumps({'type': 'text', 'content': intent['explanation_for_user']}, ensure_ascii=False)}\n\n"

        if file_is_briefing:
            yield f"data: {json.dumps({'type': 'text', 'content': '📋 Briefing detectado: ' + request.file_name}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'thinking', 'model': 'auto', 'step': 1}, ensure_ascii=False)}\n\n"

        # Queue for real-time streaming from agent thread
        evt_queue = _queue.Queue()

        def on_progress(iteration, total, message):
            """Callback fired each iteration — streams progress to SSE."""
            evt_queue.put({"type": "thinking", "model": message, "step": iteration})

        def run_in_thread():
            """Run agent loop in background thread, push result to queue."""
            try:
                from core.agent_loop import run_agent_loop, run_briefing

                if mode == "briefing":
                    import tempfile
                    briefing_content = request.file_content if file_is_briefing else None
                    briefing_path = request.input

                    if briefing_content:
                        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir='/tmp')
                        tmp.write(briefing_content)
                        tmp.close()
                        briefing_path = tmp.name

                    result = run_briefing(
                        briefing_path=briefing_path,
                        project_dir=project_dir,
                        verbose=False,
                    )

                    if briefing_content:
                        try:
                            os.unlink(briefing_path)
                        except OSError:
                            pass

                    evt_queue.put({"type": "tool_result", "tool": "run_briefing",
                                   "result": "Briefing: {}/{} pasos".format(result.get('steps_completed', 0), result.get('steps_total', 0)),
                                   "is_error": not result.get('all_passed', False)})
                    evt_queue.put({"__done__": True, "result": result})
                else:
                    result = run_agent_loop(
                        goal=goal,
                        mode="goal",
                        project_dir=project_dir,
                        strategy="tiered",
                        max_iterations=999,
                        max_cost=15.0,
                        autonomous=True,
                        verbose=False,
                        session_id=session_id,
                        on_progress=on_progress,
                    )

                    # Include model's final text as text event
                    final_text = result.get("result") or ""
                    if final_text and len(final_text) > 20:
                        evt_queue.put({"type": "text", "content": final_text[:2000]})

                    # Push tool calls from log
                    for entry in result.get("log", []):
                        if isinstance(entry, dict):
                            tool = entry.get("tool", "")
                            is_err = entry.get("is_error", False)
                            evt_queue.put({"type": "tool_call", "tool": tool, "args": {}})
                            evt_queue.put({"type": "tool_result", "tool": tool,
                                           "result": "OK" if not is_err else "ERROR", "is_error": is_err})

                    evt_queue.put({"__done__": True, "result": result})

            except Exception as e:
                evt_queue.put({"__error__": True, "message": str(e)})

        # Start agent loop in background thread
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        # Stream events from queue with keepalive heartbeats
        while True:
            try:
                evt = evt_queue.get(timeout=3)
            except _queue.Empty:
                # Keepalive to prevent proxy/browser timeout
                elapsed = int(_time.time() - start)
                yield f": keepalive {elapsed}s\n\n"
                if elapsed > 600:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout: ejecucion excedio 10 minutos'}, ensure_ascii=False)}\n\n"
                    break
                continue

            if evt.get("__done__"):
                final_result = evt["result"]
                try:
                    reporter = Reporter()
                    summary = reporter.summarize_session(final_result) if isinstance(final_result, dict) and "stop_reason" in final_result else str(final_result)
                    # Append model's actual result for richer done event
                    if isinstance(final_result, dict):
                        model_result = final_result.get("result") or ""
                        if model_result and len(model_result) > 20:
                            summary += " | " + model_result[:500]
                except Exception:
                    summary = str(final_result.get("result", "Completado")) if isinstance(final_result, dict) else str(final_result)

                elapsed_ms = int((_time.time() - start) * 1000)
                cost = final_result.get("cost_usd", final_result.get("total_cost", 0)) if isinstance(final_result, dict) else 0

                yield f"data: {json.dumps({'type': 'done', 'summary': summary, 'total_ms': elapsed_ms, 'total_cost_usd': cost, 'session_id': session_id}, ensure_ascii=False)}\n\n"

                _running_sessions[session_id] = {
                    "status": "completed" if (isinstance(final_result, dict) and final_result.get("stop_reason") == "DONE") else "done",
                    "result": final_result if isinstance(final_result, dict) else {"result": str(final_result)},
                }
                break

            elif evt.get("__error__"):
                yield f"data: {json.dumps({'type': 'error', 'message': evt['message']}, ensure_ascii=False)}\n\n"
                break

            else:
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/code-os/session/{session_id}")
async def get_session(session_id: str):
    """Get session status and result."""
    # Check in-memory first
    if session_id in _running_sessions:
        return _running_sessions[session_id]

    # Check Supabase
    db = SupabaseClient()
    if db.enabled:
        state = db.get_session_state(session_id)
        if state:
            return {"status": state.get("status", "unknown"), "result": state}

    raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


@app.get("/code-os/sessions")
async def list_sessions(project: str = "", limit: int = 10):
    """List recent sessions."""
    db = SupabaseClient()
    if not db.enabled:
        return {"sessions": list(_running_sessions.keys())[-limit:]}

    if project:
        sessions = db.get_project_history(project, limit=limit)
    else:
        result = db._request("GET", "code_os_sessions",
            params=f"order=created_at.desc&limit={limit}"
                   f"&select=id,mode,input_raw,status,project_name,created_at")
        sessions = result if isinstance(result, list) else []

    return {"sessions": sessions}


@app.get("/code-os/health")
async def code_os_health():
    """Proactive health check for CEO dashboard."""
    import datetime
    try:
        from core.proactive import health_check
        alerts = health_check()
    except Exception as e:
        alerts = [{"nivel": "error", "mensaje": f"Health check failed: {e}", "accion_sugerida": "Verificar conexion DB"}]
    return {
        "alerts": alerts,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@app.get("/code-os/status")
async def code_os_status():
    """Code OS system status for CEO dashboard."""
    from core.api import get_tier_config
    try:
        from core.proactive import health_check
        health = health_check()
    except Exception:
        health = []

    tc = get_tier_config()
    modelos = [v for k, v in tc.items() if isinstance(v, str)]

    try:
        from tools import create_default_registry
        import tempfile
        reg = create_default_registry(tempfile.gettempdir())
        tools_count = reg.tool_count()
    except Exception:
        tools_count = 63

    # Last session
    last_session = None
    if _running_sessions:
        last_key = list(_running_sessions.keys())[-1]
        last_session = {"id": last_key, "status": _running_sessions[last_key].get("status")}

    # Advanced module states (Fase 3)
    circuit_breaker_state = {}
    try:
        from core.monitoring import get_circuit_breaker
        circuit_breaker_state = get_circuit_breaker().get_estados()
    except Exception:
        pass

    monitor_state = {}
    try:
        from core.monitoring import get_monitor
        mon = get_monitor()
        monitor_state = {
            "slos": mon.check_slos(),
            "budget": mon.check_budget(),
            "dashboard": mon.get_dashboard(),
        }
    except Exception:
        pass

    criticality_state = {}
    try:
        from core.criticality_engine import get_criticality_engine
        crit = get_criticality_engine()
        criticality_state = {
            "T": crit.T,
            "T_c": crit.T_c,
            "ajuste_manifold": crit.ajustar_manifold_temperatura(),
        }
    except Exception:
        pass

    flywheel_state = {}
    try:
        from core.flywheel import check_promotion
        promo = check_promotion()
        flywheel_state = {"pending_promotion": promo}
    except Exception:
        pass

    return {
        "version": VERSION,
        "modelos_activos": modelos,
        "tools_count": tools_count,
        "last_session": last_session,
        "health": health,
        "circuit_breaker": circuit_breaker_state,
        "monitor": monitor_state,
        "criticality": criticality_state,
        "flywheel": flywheel_state,
    }


@app.get("/ceo")
async def ceo_dashboard():
    """CEO Dashboard — full system control interface."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "ceo.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="ceo.html not found")
    return FileResponse(html_path, media_type="text/html")


@app.get("/chat")
async def chat_page():
    """Serve the web chat interface."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "chat.html")
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="chat.html not found")
    return FileResponse(html_path, media_type="text/html")


@app.get("/chat/sessions")
async def chat_sessions(limit: int = 20):
    """List recent chat sessions from DB."""
    engine = _get_chat_engine()
    sessions = engine.list_sessions()
    return {"sessions": sessions[:limit]}


@app.get("/chat/session/{session_id}/history")
async def chat_session_history(session_id: str):
    """Get displayable history for session restore."""
    engine = _get_chat_engine()
    history = engine.get_session_history(session_id)
    return {"session_id": session_id, "history": history}


@app.delete("/chat/session/{session_id}")
async def chat_session_delete(session_id: str):
    """Delete a chat session."""
    engine = _get_chat_engine()
    deleted = engine.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def _extract_text(filename: str, content: bytes) -> str:
    """Extract text from uploaded file based on extension."""
    ext = os.path.splitext(filename)[1].lower()

    # Plain text formats
    if ext in (".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".toml",
               ".py", ".js", ".ts", ".html", ".css", ".sql", ".sh", ".env",
               ".xml", ".ini", ".cfg", ".conf", ".log", ".rst"):
        return content.decode("utf-8", errors="replace")

    # PDF
    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"--- Page {i+1} ---\n{text}")
            return "\n\n".join(pages) if pages else "(PDF sin texto extraible)"
        except Exception as e:
            return f"(Error leyendo PDF: {e})"

    # Word .docx
    if ext == ".docx":
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs) if paragraphs else "(DOCX vacio)"
        except Exception as e:
            return f"(Error leyendo DOCX: {e})"

    # Legacy .doc — try as text, warn if binary
    if ext == ".doc":
        try:
            text = content.decode("utf-8", errors="replace")
            # Check if it's mostly binary
            printable = sum(1 for c in text[:500] if c.isprintable() or c in "\n\r\t")
            if printable / max(len(text[:500]), 1) < 0.5:
                return "(Formato .doc binario no soportado. Convierte a .docx o .pdf)"
            return text
        except Exception:
            return "(Formato .doc no soportado. Convierte a .docx o .pdf)"

    # Fallback — try as text
    try:
        text = content.decode("utf-8", errors="replace")
        return text
    except Exception:
        return f"(Formato {ext} no soportado)"


@app.post("/chat/upload")
async def chat_upload(
    chat_id: str = Form(...),
    message: str = Form(""),
    file: UploadFile = File(...),
    force_phase: Optional[str] = Form(None),
):
    """Upload a document + optional message, extract text, process as chat message."""
    # Read file
    file_content = await file.read()
    if len(file_content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (max 10MB)")

    # Extract text
    extracted = _extract_text(file.filename or "unknown.txt", file_content)

    # Truncate if too long (LLM context limits)
    if len(extracted) > 50000:
        extracted = extracted[:50000] + f"\n\n... (truncado, {len(extracted)} chars total)"

    # Build combined message
    fname = file.filename or "documento"
    combined = f"[Documento adjunto: {fname}]\n\n{extracted}"
    if message.strip():
        combined = f"{message}\n\n{combined}"

    engine = _get_chat_engine()

    def event_stream():
        # Emit file_received event first
        yield f"data: {json.dumps({'type': 'file_received', 'filename': fname, 'size': len(file_content), 'chars': len(extracted)}, ensure_ascii=False)}\n\n"
        for event in engine.process_message(
            chat_id, combined, force_phase=force_phase,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat/send")
async def chat_send(request: ChatRequest):
    """Process a chat message and return SSE event stream."""
    engine = _get_chat_engine()

    # Override project dir if specified
    if request.project:
        engine.project_dir = os.path.abspath(request.project)

    def event_stream():
        for event in engine.process_message(
            request.chat_id, request.message, force_phase=request.force_phase,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---- Universidad I+D Explorer ---- #

class ExploreRequest(BaseModel):
    scope_a: str
    scope_b: str
    max_pairs: int = 5
    mode: str = "fast"  # "fast" or "swarm"


@app.post("/explorer/run")
async def explorer_run(request: ExploreRequest):
    """Run autonomous pattern exploration. Returns SSE stream with discoveries."""
    from tools.explorer import run_exploration

    max_pairs = min(request.max_pairs, 10)
    mode = request.mode if request.mode in ("fast", "swarm") else "fast"

    def event_stream():
        for event in run_exploration(request.scope_a, request.scope_b, max_pairs,
                                     mode=mode):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/explorer/discoveries")
async def explorer_discoveries(limit: int = 20, tipo: str = ""):
    """Get recent discoveries from pattern exploration."""
    from tools.explorer import tool_get_discoveries
    result = tool_get_discoveries(limit, tipo)
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return {"discoveries": result}


@app.get("/explorer/classifications")
async def explorer_classifications(scope_a: str = "", scope_b: str = "",
                                    limit: int = 20):
    """Get structural classifications between pattern pairs."""
    from tools.explorer import tool_get_classifications
    result = tool_get_classifications(scope_a, scope_b, limit)
    try:
        return json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return {"classifications": result}


@app.get("/explorer/scopes")
async def explorer_scopes():
    """List available pattern scopes for exploration."""
    from tools.database import _get_conn
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT scope, count(*) as count
                FROM knowledge_base
                WHERE scope LIKE 'patrones:%%'
                GROUP BY scope
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
        return {"scopes": rows}
    except Exception as e:
        return {"scopes": [], "error": str(e)}
    finally:
        conn.close()


# ---- Swarm Algebra (Enjambre + Pizarra) ---- #

class SwarmAnalyzeRequest(BaseModel):
    patron_a_id: int
    patron_b_id: int
    operacion: str = "auto"


@app.post("/explorer/swarm-analyze")
async def explorer_swarm_analyze(request: SwarmAnalyzeRequest):
    """Analyze a pattern pair using multi-model swarm with pizarra. Returns SSE stream."""
    from tools.swarm_algebra import run_swarm_analysis

    def event_stream():
        for event in run_swarm_analysis(
            request.patron_a_id, request.patron_b_id, request.operacion
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/explorer/pizarra/{pizarra_id}")
async def explorer_pizarra(pizarra_id: int):
    """Get a persisted pizarra snapshot."""
    from tools.database import _get_conn
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM pizarras_algebra WHERE id = %s
            """, [pizarra_id])
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pizarra not found")
        return row
    finally:
        conn.close()


@app.get("/explorer/estimate")
async def explorer_estimate(scope_a: str, scope_b: str, max_pairs: int = 5,
                            mode: str = "swarm"):
    """Estimate cost of an exploration before running it."""
    from tools.explorer import classify_scope_pairs

    cost_per_pair = 3.65 if mode == "swarm" else 0.05
    classifications = classify_scope_pairs(scope_a, scope_b, limit=max_pairs * 3)

    # Select top pairs (same logic as run_exploration)
    by_type = {}
    for cls in classifications:
        t = cls["clasificacion"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(cls)

    selected = []
    for cls_type, pairs in by_type.items():
        n = max(1, max_pairs // len(by_type))
        selected.extend(pairs[:n])
    selected = selected[:max_pairs]

    breakdown = []
    for i, pair in enumerate(selected):
        breakdown.append({
            "index": i,
            "patron_a_id": pair["patron_a_id"],
            "patron_b_id": pair["patron_b_id"],
            "patron_a": pair.get("patron_a_texto", "")[:80],
            "patron_b": pair.get("patron_b_texto", "")[:80],
            "classification": pair["clasificacion"],
            "score": pair["score"],
            "cost_usd": cost_per_pair,
        })

    return {
        "total_pairs_possible": len(classifications),
        "selected_pairs": len(selected),
        "estimated_cost_usd": round(len(selected) * cost_per_pair, 2),
        "cost_per_pair": cost_per_pair,
        "mode": mode,
        "breakdown": breakdown,
    }


@app.get("/explorer/checklist")
async def explorer_checklist(limit: int = 20):
    """List all explorations with progress and cost tracking."""
    from tools.database import _get_conn
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT e.*,
                    (SELECT count(*) FROM emergencias_descubiertas ed
                     JOIN relaciones_patrones rp ON ed.relacion_id = rp.id
                     WHERE rp.id IN (
                         SELECT rp2.id FROM relaciones_patrones rp2
                         WHERE rp2.estrategia_razonamiento->>'exploration_id' = e.id::text
                     )) as discoveries_count,
                    (SELECT count(*) FROM emergencias_descubiertas ed2
                     WHERE ed2.promovido_a_patron = TRUE
                     AND ed2.relacion_id IN (
                         SELECT rp3.id FROM relaciones_patrones rp3
                         WHERE rp3.estrategia_razonamiento->>'exploration_id' = e.id::text
                     )) as promoted_count
                FROM exploraciones e
                ORDER BY e.started_at DESC
                LIMIT %s
            """, [limit])
            rows = cur.fetchall()
        return {"explorations": rows}
    except Exception as e:
        return {"explorations": [], "error": str(e)}
    finally:
        conn.close()


# ---- Taxonomy (Matrices multidimensionales) ---- #

@app.get("/explorer/matrix")
async def explorer_matrix():
    """Get taxonomy matrices: Lente x Funcion + Thinking x Mode with pattern counts."""
    from tools.database import _get_conn
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Lente x Funcion matrix
            cur.execute("""
                SELECT lente_funcion_primary, count(*) as count
                FROM knowledge_base
                WHERE lente_funcion_primary IS NOT NULL
                GROUP BY lente_funcion_primary
                ORDER BY count DESC
            """)
            lf_rows = cur.fetchall()

            # Thinking x Mode matrix
            cur.execute("""
                SELECT thinking_primary, mode_primary, count(*) as count
                FROM knowledge_base
                WHERE thinking_primary IS NOT NULL AND mode_primary IS NOT NULL
                GROUP BY thinking_primary, mode_primary
                ORDER BY count DESC
            """)
            tm_rows = cur.fetchall()

            # Total classified
            cur.execute("""
                SELECT count(*) as total,
                    count(lente_funcion_primary) as with_lente_funcion,
                    count(thinking_primary) as with_thinking,
                    count(mode_primary) as with_mode
                FROM knowledge_base
                WHERE scope LIKE 'patrones:%%'
            """)
            totals = cur.fetchone()

        return {
            "lente_funcion": lf_rows,
            "thinking_mode": tm_rows,
            "totals": totals,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


@app.get("/explorer/by-dimension")
async def explorer_by_dimension(
    lente: str = "", funcion: str = "", thinking: str = "",
    mode: str = "", scope: str = "", limit: int = 50
):
    """Filter patterns by taxonomy dimensions."""
    from tools.database import _get_conn
    import psycopg2.extras
    conn = _get_conn()
    try:
        conditions = ["scope LIKE 'patrones:%%'"]
        params = []
        if lente:
            conditions.append("%s = ANY(lentes)")
            params.append(lente)
        if funcion:
            conditions.append("%s = ANY(funciones)")
            params.append(funcion)
        if thinking:
            conditions.append("%s = ANY(thinking_types)")
            params.append(thinking)
        if mode:
            conditions.append("%s = ANY(conceptual_modes)")
            params.append(mode)
        if scope:
            conditions.append("scope = %s")
            params.append(scope)

        params.append(limit)
        where = " AND ".join(conditions)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT id, scope, tipo, texto,
                    lentes, funciones, thinking_types, conceptual_modes,
                    lente_funcion_primary, thinking_primary, mode_primary
                FROM knowledge_base
                WHERE {where}
                ORDER BY id
                LIMIT %s
            """, params)
            rows = cur.fetchall()

        # Truncate texto for response
        for r in rows:
            if r.get("texto") and len(r["texto"]) > 200:
                r["texto"] = r["texto"][:200] + "..."

        return {"patterns": rows, "count": len(rows)}
    except Exception as e:
        return {"patterns": [], "error": str(e)}
    finally:
        conn.close()


@app.get("/explorer/gaps")
async def explorer_gaps():
    """Find empty or under-represented cells in taxonomy matrices."""
    from tools.database import _get_conn
    conn = _get_conn()
    try:
        lentes = ["salud", "sentido", "continuidad"]
        funciones = ["conservar", "captar", "depurar", "distribuir", "frontera", "adaptar", "replicar"]
        thinkings = [
            "percepcion", "causalidad", "abstraccion", "sintesis", "discernimiento",
            "metacognicion", "consciencia_epistemologica", "auto_diagnostico",
            "convergencia", "dialectica", "analogia", "contrafactual", "abduccion",
            "provocacion", "reencuadre", "destruccion_creativa", "creacion"
        ]
        modes = ["ANALIZAR", "PERCIBIR", "MOVER", "SENTIR", "GENERAR", "ENMARCAR"]

        with conn.cursor() as cur:
            # Check lente x funcion gaps
            lf_gaps = []
            for l in lentes:
                for f in funciones:
                    key = f"{l}:{f}"
                    cur.execute("""
                        SELECT count(*) FROM knowledge_base
                        WHERE lente_funcion_primary = %s
                    """, [key])
                    count = cur.fetchone()[0]
                    if count < 2:
                        lf_gaps.append({"lente": l, "funcion": f, "count": count})

            # Check thinking gaps
            t_gaps = []
            for t in thinkings:
                cur.execute("""
                    SELECT count(*) FROM knowledge_base
                    WHERE thinking_primary = %s
                """, [t])
                count = cur.fetchone()[0]
                if count < 2:
                    t_gaps.append({"thinking": t, "count": count})

            # Check mode gaps
            m_gaps = []
            for m in modes:
                cur.execute("""
                    SELECT count(*) FROM knowledge_base
                    WHERE mode_primary = %s
                """, [m])
                count = cur.fetchone()[0]
                if count < 3:
                    m_gaps.append({"mode": m, "count": count})

        return {
            "lente_funcion_gaps": lf_gaps,
            "thinking_gaps": t_gaps,
            "mode_gaps": m_gaps,
            "total_lf_gaps": len(lf_gaps),
            "total_thinking_gaps": len(t_gaps),
            "total_mode_gaps": len(m_gaps),
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


# ---- Protocol (6 Chapters) ---- #

@app.get("/chat/protocol/{chat_id}")
async def chat_protocol(chat_id: str):
    """Get protocol progress for a chat session."""
    engine = _get_chat_engine()
    session = engine.sessions.get(chat_id)
    if not session:
        return {"error": "Session not found"}
    protocol = session.get("protocol")
    if not protocol:
        return {"error": "No protocol engine for this session"}
    return protocol.get_progress()


@app.post("/chat/protocol/{chat_id}/advance")
async def chat_protocol_advance(chat_id: str):
    """Advance to the next chapter in the protocol."""
    engine = _get_chat_engine()
    session = engine.sessions.get(chat_id)
    if not session:
        return {"error": "Session not found"}
    protocol = session.get("protocol")
    if not protocol:
        return {"error": "No protocol engine"}
    new_chapter = protocol.advance_chapter()
    if new_chapter:
        return {"advanced_to": new_chapter, "progress": protocol.get_progress()}
    return {"error": "Already at last chapter"}


# ---- Neural DB ---- #

class NeuralSearchRequest(BaseModel):
    query: str
    limit: int = 10
    scope: Optional[str] = None
    session_id: Optional[str] = None


@app.post("/neural/search")
async def neural_search(request: NeuralSearchRequest):
    """Semantic search with Hebbian boost."""
    from core.neural_db import get_neural_db
    ndb = get_neural_db()
    results = ndb.semantic_search(
        request.query, limit=request.limit,
        scope=request.scope, session_id=request.session_id
    )
    for r in results:
        if r.get("texto") and len(r["texto"]) > 300:
            r["texto"] = r["texto"][:300] + "..."
    return {"results": results, "count": len(results)}


@app.get("/neural/related/{knowledge_id}")
async def neural_related(knowledge_id: int, min_strength: float = 0.2, limit: int = 10):
    """Get knowledge related by Hebbian connection strength."""
    from core.neural_db import get_neural_db
    ndb = get_neural_db()
    results = ndb.get_related(knowledge_id, min_strength=min_strength, limit=limit)
    for r in results:
        if r.get("texto") and len(r["texto"]) > 300:
            r["texto"] = r["texto"][:300] + "..."
    return {"related": results, "count": len(results)}


@app.get("/neural/stats")
async def neural_stats():
    """Connection network statistics."""
    from core.neural_db import get_neural_db
    ndb = get_neural_db()
    return ndb.get_connection_stats()


@app.post("/neural/decay")
async def neural_decay():
    """Apply weekly decay to connections. Call periodically."""
    from core.neural_db import get_neural_db
    ndb = get_neural_db()
    decayed = ndb.decay_connections()
    return {"decayed": decayed}


# ---- Model Observatory ---- #

@app.get("/models/registry")
async def models_registry():
    """List all models in the registry with their status, tier, and scores."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.get_market_report()


@app.get("/models/discover")
async def models_discover():
    """Discover new models from OpenRouter API and add as candidates."""
    try:
        from core.model_observatory import get_observatory
        obs = get_observatory()
        return obs.discover_models()
    except Exception as e:
        return {"status": "degraded", "error": str(e),
                "message": "Discovery temporarily unavailable. Use /models/registry for registered models."}


@app.get("/models/health")
async def models_health():
    """Health check all active models."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.health_check_all()


class BenchmarkRequest(BaseModel):
    model_id: str
    benchmark: str = "tool_use"


@app.post("/models/benchmark")
async def models_benchmark(request: BenchmarkRequest):
    """Run internal benchmark against a model."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.run_benchmark(request.model_id, request.benchmark)


class ABTestRequest(BaseModel):
    tier: str
    model_b: str
    test_name: Optional[str] = None


@app.post("/models/ab-test")
async def models_ab_test(request: ABTestRequest):
    """Start A/B test between current tier champion and challenger."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.start_ab_test(request.tier, request.model_b, request.test_name)


class PromoteRequest(BaseModel):
    model_id: str
    tier: str


@app.post("/models/promote")
async def models_promote(request: PromoteRequest):
    """Promote a model to active for a specific tier."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.promote_model(request.model_id, request.tier)


@app.get("/models/report")
async def models_report():
    """Full market report: active vs candidates, health, costs."""
    from core.model_observatory import get_observatory
    obs = get_observatory()
    return obs.get_market_report()


# ---- Tool Evolution ---- #

@app.get("/tools/stats")
async def tools_stats(tool_name: str = None, days: int = 30):
    """Get tool usage statistics."""
    from core.tool_evolution import get_tool_evolution
    engine = get_tool_evolution()
    return engine.get_tool_stats(tool_name=tool_name, days=days)


@app.get("/tools/rankings")
async def tools_rankings():
    """Tool rankings: most used, effective, costly, slowest."""
    from core.tool_evolution import get_tool_evolution
    engine = get_tool_evolution()
    return engine.get_tool_rankings()


@app.get("/tools/gaps")
async def tools_gaps(limit: int = 10):
    """Top tool gaps by frequency."""
    from core.tool_evolution import get_tool_evolution
    engine = get_tool_evolution()
    return {"gaps": engine.get_top_gaps(limit=limit)}


@app.get("/tools/compositions")
async def tools_compositions():
    """List active tool compositions/workflows."""
    from core.tool_evolution import get_tool_evolution
    engine = get_tool_evolution()
    return {"compositions": engine.get_compositions()}


@app.get("/tools/evolution-report")
async def tools_evolution_report():
    """Full evolution report: stats, gaps, compositions, trends."""
    from core.tool_evolution import get_tool_evolution
    engine = get_tool_evolution()
    return engine.evolution_report()


# ---- Reasoning Council ---- #

@app.post("/council/validate")
async def council_validate(request: Request):
    """Validate a proposal through the Reasoning Council (Nemotron + Step + Cogito)."""
    from core.router import ReasoningCouncil
    body = await request.json()
    proposal = body.get("proposal", "")
    context = body.get("context", "")
    if not proposal:
        return {"error": "proposal required"}
    council = ReasoningCouncil()
    return council.convene(proposal, context)


@app.post("/ingest")
async def ingest_endpoint(request: Request):
    """Ingest a folder into knowledge_base. Safe: never deletes unless mode=full."""
    body = await request.json()
    path = body.get("path", "/repo")
    scope = body.get("scope", "repo")
    mode = body.get("mode", "incremental")

    if mode not in ("incremental", "full"):
        return {"error": "mode must be 'incremental' or 'full'"}
    if not os.path.isdir(path):
        return {"error": f"Not a directory: {path}"}

    from ingest import ingest_folder
    stats = ingest_folder(path, scope_prefix=scope, mode=mode)
    return {"status": "ok", **stats}


# ---- Gestor de la Matriz (SN-04) ---- #

@app.post("/gestor/gradientes")
async def gradientes_endpoint(request: Request):
    """Calcula campo de gradientes para un input."""
    body = await request.json()
    input_texto = body.get("input", "")
    if not input_texto:
        return {"error": "Falta 'input'"}
    from core.gestor import calcular_gradientes
    return calcular_gradientes(input_texto)


@app.post("/gestor/compilar")
async def compilar_endpoint(request: Request):
    """Compila programa de preguntas para un patron de gaps."""
    body = await request.json()
    input_texto = body.get("input", "")
    consumidor = body.get("consumidor", "motor_vn")
    if not input_texto:
        return {"error": "Falta 'input'"}
    from core.gestor import calcular_gradientes, compilar_programa
    gradientes = calcular_gradientes(input_texto)
    programa = compilar_programa(gradientes, consumidor)
    return {"gradientes": gradientes, "programa": programa}


@app.get("/gestor/programas")
async def programas_endpoint(consumidor: str = None):
    """Lista programas compilados activos."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            if consumidor:
                cur.execute("""
                    SELECT id, consumidor, tasa_cierre_media, n_ejecuciones, compilado_at
                    FROM programas_compilados
                    WHERE consumidor = %s AND activo = true
                    ORDER BY tasa_cierre_media DESC
                """, [consumidor])
            else:
                cur.execute("""
                    SELECT id, consumidor, tasa_cierre_media, n_ejecuciones, compilado_at
                    FROM programas_compilados WHERE activo = true
                    ORDER BY consumidor, tasa_cierre_media DESC
                """)
            cols = ['id', 'consumidor', 'tasa_cierre_media', 'n_ejecuciones', 'compilado_at']
            return {"programas": [dict(zip(cols, r)) for r in cur.fetchall()]}
    finally:
        put_conn(conn)


@app.post("/gestor/registrar-efectividad")
async def registrar_efectividad_endpoint(request: Request):
    """Registra datapoint de efectividad."""
    body = await request.json()
    from core.gestor import registrar_efectividad
    registrar_efectividad(
        pregunta_id=body['pregunta_id'],
        modelo=body['modelo'],
        caso_id=body['caso_id'],
        consumidor=body.get('consumidor', 'motor_vn'),
        celda_objetivo=body['celda_objetivo'],
        gap_pre=body['gap_pre'],
        gap_post=body['gap_post'],
        operacion=body.get('operacion', 'individual'),
    )
    return {"status": "ok"}


# ---- Mejora Continua y Estigmergia (SN-05) ---- #

@app.post("/mejora/detectar")
async def detectar_mejoras_endpoint():
    """Ejecuta deteccion de mejoras."""
    from core.mejora_continua import detectar_mejoras
    mejoras = detectar_mejoras()
    return {"mejoras_detectadas": len(mejoras), "detalle": mejoras}


@app.get("/mejora/cola")
async def cola_mejoras_endpoint(estado: str = "pendiente"):
    """Lista mejoras en cola."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, tipo, descripcion, prioridad, estado, created_at
                FROM cola_mejoras WHERE estado = %s
                ORDER BY prioridad DESC, created_at
            """, [estado])
            cols = ['id', 'tipo', 'descripcion', 'prioridad', 'estado', 'created_at']
            return {"mejoras": [dict(zip(cols, r)) for r in cur.fetchall()]}
    finally:
        put_conn(conn)


@app.post("/estigmergia/marca")
async def crear_marca_endpoint(request: Request):
    """Crea marca estigmergica."""
    body = await request.json()
    from core.mejora_continua import crear_marca_estigmergica
    crear_marca_estigmergica(body['tipo'], body['origen'], body.get('contenido', {}))
    return {"status": "ok"}


@app.get("/estigmergia/marcas")
async def marcas_endpoint(tipo: str = None, consumir: bool = False):
    """Lee marcas estigmergicas."""
    if consumir:
        from core.mejora_continua import consumir_marcas
        return {"marcas": consumir_marcas(tipo)}
    else:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"error": "No DB"}
        try:
            with conn.cursor() as cur:
                if tipo:
                    cur.execute("""
                        SELECT id, tipo, origen, contenido, consumida, created_at
                        FROM marcas_estigmergicas WHERE tipo = %s
                        ORDER BY created_at DESC LIMIT 50
                    """, [tipo])
                else:
                    cur.execute("""
                        SELECT id, tipo, origen, contenido, consumida, created_at
                        FROM marcas_estigmergicas
                        ORDER BY created_at DESC LIMIT 50
                    """)
                cols = ['id', 'tipo', 'origen', 'contenido', 'consumida', 'created_at']
                return {"marcas": [dict(zip(cols, r)) for r in cur.fetchall()]}
        finally:
            put_conn(conn)


@app.get("/gestor/log")
async def log_gestor_endpoint(limit: int = 50):
    """Log de acciones del Gestor."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, accion, detalle, nivel, created_at
                FROM log_gestor ORDER BY created_at DESC LIMIT %s
            """, [limit])
            cols = ['id', 'accion', 'detalle', 'nivel', 'created_at']
            return {"log": [dict(zip(cols, r)) for r in cur.fetchall()]}
    finally:
        put_conn(conn)


# ---- Telemetria y Propiocepcion (SN-03) ---- #

@app.get("/propiocepcion")
async def propiocepcion_endpoint():
    """Estado completo del sistema nervioso."""
    from core.telemetria import propiocepcion
    return propiocepcion()


@app.get("/senales")
async def senales_endpoint(resueltas: bool = False, limit: int = 50):
    """Señales del sistema (alertas, umbrales, anomalias)."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, tipo, severidad, mensaje, datos, created_at
                FROM señales
                WHERE resuelta = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, [resueltas, limit])
            cols = ['id', 'tipo', 'severidad', 'mensaje', 'datos', 'created_at']
            return {"señales": [dict(zip(cols, r)) for r in cur.fetchall()]}
    finally:
        put_conn(conn)


@app.post("/senales/{senal_id}/resolver")
async def resolver_senal(senal_id: int):
    """Marcar señal como resuelta."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE señales SET resuelta = true WHERE id = %s", [senal_id])
        conn.commit()
        return {"status": "ok"}
    finally:
        put_conn(conn)


@app.get("/metricas")
async def metricas_endpoint(componente: str = None, horas: int = 24, limit: int = 100):
    """Metricas del sistema."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        with conn.cursor() as cur:
            if componente:
                cur.execute("""
                    SELECT id, componente, evento, datos, created_at
                    FROM metricas
                    WHERE componente = %s AND created_at > NOW() - make_interval(hours => %s)
                    ORDER BY created_at DESC LIMIT %s
                """, [componente, horas, limit])
            else:
                cur.execute("""
                    SELECT id, componente, evento, datos, created_at
                    FROM metricas
                    WHERE created_at > NOW() - make_interval(hours => %s)
                    ORDER BY created_at DESC LIMIT %s
                """, [horas, limit])
            cols = ['id', 'componente', 'evento', 'datos', 'created_at']
            return {"metricas": [dict(zip(cols, r)) for r in cur.fetchall()]}
    finally:
        put_conn(conn)


@app.post("/evaluar-reglas")
async def evaluar_reglas_endpoint():
    """Evalua reglas de deteccion contra metricas actuales."""
    from core.telemetria import evaluar_reglas
    señales = evaluar_reglas()
    return {"señales_generadas": len(señales), "detalle": señales}


@app.get("/health")
async def health():
    """Health check."""
    db = SupabaseClient()
    return {
        "status": "ok",
        "version": VERSION,
        "tools": 61,
        "supabase": db.enabled,
        "swarm_models": 4,  # 3 explorers + 1 synthesizer
        "model_observatory": True,
        "running_sessions": sum(1 for s in _running_sessions.values()
                               if s["status"] == "running"),
    }


# ==========================================
# SN-06: Registrador PID
# ==========================================

@app.post("/motor/registrar")
async def motor_registrar(request: Request):
    """Registra un datapoint de ejecucion y retorna señales PID."""
    try:
        body = await request.json()
        from core.registrador import registrar_ejecucion
        resultado = registrar_ejecucion(body)
        return {"status": "ok", "señales": resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/motor/señales/{celda}")
async def motor_señales_celda(celda: str):
    """Consulta señales PID para una celda especifica.

    Ejemplo: GET /motor/señales/ConservarxSalud
    """
    try:
        from core.registrador import computar_señales_pid
        señales = computar_señales_pid(celda)
        return {"status": "ok", "celda": celda, "señales": señales}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/motor/señales")
async def motor_señales_todas():
    """Consulta señales PID para todas las celdas activas."""
    try:
        from core.registrador import obtener_señales_todas_celdas
        señales = obtener_señales_todas_celdas()
        return {"status": "ok", "celdas": len(señales), "señales": señales}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-07: Gestor GAMC
# ==========================================

@app.post("/gestor/loop")
async def gestor_loop():
    """Ejecuta el loop completo del Gestor GAMC (10 pasos + auto-ajuste)."""
    try:
        from core.gestor import get_gestor
        gestor = get_gestor()
        resultado = gestor.ejecutar_loop()
        return {"status": "ok", "resultado": resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/salud")
async def gestor_salud():
    """Estado completo de la Matriz."""
    try:
        from core.gestor import get_gestor
        gestor = get_gestor()
        salud = gestor.obtener_salud()
        return {"status": "ok", "salud": salud}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/parametros")
async def gestor_parametros():
    """Parametros actuales del controlador GAMC."""
    try:
        from core.gestor import get_gestor
        gestor = get_gestor()
        return {
            "status": "ok",
            "parametros": dict(gestor.params),
            "ciclo": gestor.ciclo_n,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-08: Constraint Manifold (13 Reglas)
# ==========================================

@app.post("/gestor/validar-programa")
async def gestor_validar_programa(request: Request):
    """Valida un programa contra las 13 reglas del compilador."""
    try:
        body = await request.json()
        from core.reglas_compilador import get_manifold
        manifold = get_manifold()
        valido, violaciones = manifold.validar(body)
        return {
            "status": "ok",
            "valido": valido,
            "violaciones": violaciones,
            "n_violaciones": len(violaciones),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/gestor/corregir-programa")
async def gestor_corregir_programa(request: Request):
    """Proyecta un programa invalido al punto mas cercano valido."""
    try:
        body = await request.json()
        from core.reglas_compilador import get_manifold
        manifold = get_manifold()

        # Validar primero
        valido_antes, violaciones_antes = manifold.validar(body)

        # Proyectar
        corregido = manifold.proyectar(body)

        # Validar el corregido
        valido_despues, violaciones_despues = manifold.validar(corregido)

        return {
            "status": "ok",
            "programa_original": body,
            "programa_corregido": corregido,
            "valido_antes": valido_antes,
            "valido_despues": valido_despues,
            "violaciones_corregidas": len(violaciones_antes) - len(violaciones_despues),
            "violaciones_restantes": violaciones_despues,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-09: Motor vN (SFCE + Dual Process)
# ==========================================

@app.post("/motor/ejecutar-vn")
async def motor_ejecutar_vn(request: Request):
    """Ejecuta el Motor vN con pipeline SFCE completo.

    Body:
        {"input": "texto", "modo": "analisis|conversacion|generacion|confrontacion"}
    """
    try:
        body = await request.json()
        input_texto = body.get('input', '')
        modo = body.get('modo', 'analisis')

        if not input_texto:
            return {"status": "error", "error": "input requerido"}
        if modo not in ('analisis', 'conversacion', 'generacion', 'confrontacion'):
            return {"status": "error", "error": f"modo invalido: {modo}"}

        consumidor = body.get('consumidor', 'motor_vn')

        from core.motor_vn import get_motor
        motor = get_motor()
        resultado = await motor.ejecutar(input_texto, modo=modo, consumidor=consumidor)
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-11: Reactor vN
# ==========================================

@app.post("/reactor/ejecutar")
async def reactor_ejecutar():
    """Ejecutar pipeline del Reactor: generar preguntas candidatas desde gaps."""
    try:
        from core.reactor_vn import get_reactor
        reactor = get_reactor()
        resultado = reactor.ejecutar()
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/reactor/candidatas")
async def reactor_candidatas():
    """Listar preguntas candidatas pendientes de aprobacion."""
    try:
        from core.reactor_vn import get_reactor
        reactor = get_reactor()
        candidatas = reactor.listar_candidatas()
        return {"status": "ok", "candidatas": candidatas, "n": len(candidatas)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/reactor/aprobar/{pregunta_id}")
async def reactor_aprobar(pregunta_id: str):
    """Aprobar pregunta candidata (promover a nivel 'base')."""
    try:
        from core.reactor_vn import get_reactor
        reactor = get_reactor()
        resultado = reactor.aprobar_candidata(pregunta_id)
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-12: Gestor Pasos 8-10 (endpoints)
# ==========================================

@app.get("/gestor/obsoletas")
async def gestor_obsoletas():
    """Listar preguntas obsoletas."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"error": "No DB"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, inteligencia, lente, funcion, texto, created_at
                    FROM preguntas_matriz WHERE nivel = 'obsoleta'
                    ORDER BY created_at DESC LIMIT 100
                """)
                cols = ['id', 'inteligencia', 'lente', 'funcion', 'texto', 'created_at']
                return {"obsoletas": [dict(zip(cols, r)) for r in cur.fetchall()]}
        finally:
            put_conn(conn)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/contradicciones")
async def gestor_contradicciones():
    """Listar contradicciones detectadas (marcas estigmergicas tipo 'contradiccion')."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"error": "No DB"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, contenido, created_at
                    FROM marcas_estigmergicas
                    WHERE tipo = 'contradiccion'
                    ORDER BY created_at DESC LIMIT 50
                """)
                return {"contradicciones": [
                    {'id': r[0], 'contenido': r[1], 'created_at': str(r[2])}
                    for r in cur.fetchall()
                ]}
        finally:
            put_conn(conn)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/expiradas")
async def gestor_expiradas():
    """Listar preguntas expiradas."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"error": "No DB"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, inteligencia, lente, funcion, texto, created_at
                    FROM preguntas_matriz WHERE nivel = 'expirada'
                    ORDER BY created_at DESC LIMIT 100
                """)
                cols = ['id', 'inteligencia', 'lente', 'funcion', 'texto', 'created_at']
                return {"expiradas": [dict(zip(cols, r)) for r in cur.fetchall()]}
        finally:
            put_conn(conn)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-13: Sinema
# ==========================================

@app.post("/motor/ejecutar-sinema")
async def motor_ejecutar_sinema(request: Request):
    """Ejecutar Motor vN con Sinema forzado (inputs ambiguos/metaforicos).

    Body: {"input": "texto"}
    """
    try:
        body = await request.json()
        input_texto = body.get('input', '')
        if not input_texto:
            return {"status": "error", "error": "input requerido"}

        from core.sinema import get_sinema
        sinema = get_sinema()
        ambiguedad = sinema.detectar_ambiguedad(input_texto)

        from core.motor_vn import get_motor
        motor = get_motor()
        resultado = await motor.ejecutar(input_texto, modo='analisis')

        return {
            "status": "ok",
            "ambiguedad": round(ambiguedad, 2),
            "sinema_activo": ambiguedad > 0.5,
            **resultado,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-14: Propagacion
# ==========================================

@app.post("/gestor/propagar")
async def gestor_propagar(request: Request):
    """Propagar cambios manualmente.

    Body: {"tabla": "preguntas_matriz", "cambios": [{"tipo": "update", "ids": [...]}]}
    """
    try:
        body = await request.json()
        from core.propagador import get_propagador
        prop = get_propagador()
        resultado = prop.propagar(
            body.get('tabla', 'preguntas_matriz'),
            body.get('cambios', []),
        )
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/consistencia")
async def gestor_consistencia():
    """Verificar consistencia cross-table."""
    try:
        from core.propagador import get_propagador
        prop = get_propagador()
        checks = prop.verificar_consistencia()
        return {"status": "ok", **checks}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-15: Exocortex ETL + API Gateway
# ==========================================

@app.post("/exocortex/ingest")
async def exocortex_ingest(request: Request):
    """Ingestar datos externos via ETL.

    Body: {"observaciones": [{"texto": "...", "celda": "...", "inteligencia": "..."}], "tenant_id": "default"}
    """
    try:
        body = await request.json()
        from core.exocortex_etl import get_etl
        etl = get_etl()
        resultado = etl.ingest(body, tenant_id=body.get('tenant_id', 'default'))
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/exocortex/tenants")
async def exocortex_tenants():
    """Listar tenants activos."""
    try:
        from core.exocortex_etl import get_etl
        etl = get_etl()
        tenants = etl.listar_tenants()
        return {"status": "ok", "tenants": tenants, "n": len(tenants)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/webhook/observacion")
async def webhook_observacion(request: Request):
    """Webhook para observaciones real-time."""
    try:
        body = await request.json()
        from core.exocortex_etl import get_etl
        etl = get_etl()
        resultado = etl.ingest(
            {'observaciones': [body]},
            tenant_id=body.get('tenant_id', 'webhook'),
        )
        return {"status": "ok", **resultado}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-16: Monitoring + Circuit Breaker
# ==========================================

@app.get("/monitoring/dashboard")
async def monitoring_dashboard():
    """Dashboard de metricas 24h."""
    try:
        from core.monitoring import get_monitor
        monitor = get_monitor()
        return {"status": "ok", **monitor.get_dashboard()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/monitoring/slos")
async def monitoring_slos():
    """Estado de SLOs."""
    try:
        from core.monitoring import get_monitor
        monitor = get_monitor()
        return {"status": "ok", **monitor.check_slos()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/monitoring/budget")
async def monitoring_budget():
    """Presupuesto gastado."""
    try:
        from core.monitoring import get_monitor
        monitor = get_monitor()
        return {"status": "ok", **monitor.check_budget()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/monitoring/circuit-breakers")
async def monitoring_circuit_breakers():
    """Estado de circuit breakers por modelo."""
    try:
        from core.monitoring import get_circuit_breaker
        cb = get_circuit_breaker()
        return {"status": "ok", "breakers": cb.get_estados()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-17: Test Suite
# ==========================================

@app.post("/test-suite/run")
async def test_suite_run():
    """Ejecutar suite completa de invariantes."""
    try:
        from tests.test_invariants import run_all_invariants
        resultados = run_all_invariants()
        return {"status": "ok", **resultados}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# SN-18: Integration — Dashboard, API Index, Version
# ==========================================

@app.get("/api/index")
async def api_index():
    """Indice de todos los endpoints disponibles."""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method in ('GET', 'POST', 'PUT', 'DELETE'):
                    routes.append({
                        'method': method,
                        'path': route.path,
                        'name': route.name or '',
                    })
    routes.sort(key=lambda r: r['path'])
    return {"endpoints": routes, "total": len(routes)}


@app.get("/dashboard")
async def dashboard():
    """Estado unificado del sistema completo."""
    resultado = {}

    # Health
    try:
        db = SupabaseClient()
        resultado['health'] = {
            'status': 'ok',
            'version': VERSION,
            'supabase': db.enabled,
        }
    except Exception:
        resultado['health'] = {'status': 'degraded'}

    # Autopoiesis
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        resultado['autopoiesis'] = scheduler.check_autopoiesis()
        resultado['scheduler'] = {
            'running': scheduler.running,
            'intervalo_h': scheduler.intervalo_actual_h,
            'ciclos': len(scheduler.flywheel_history),
        }
    except Exception as e:
        resultado['autopoiesis'] = {'error': str(e)}

    # SLOs
    try:
        from core.monitoring import get_monitor
        monitor = get_monitor()
        resultado['slos'] = monitor.check_slos()
        resultado['budget'] = monitor.check_budget()
    except Exception as e:
        resultado['slos'] = {'error': str(e)}

    # Matriz
    try:
        from core.gestor import get_gestor
        gestor = get_gestor()
        resultado['matriz'] = {
            'ciclo_gamc': gestor.ciclo_n,
            'params': dict(gestor.params),
        }
    except Exception as e:
        resultado['matriz'] = {'error': str(e)}

    # Consistencia
    try:
        from core.propagador import get_propagador
        prop = get_propagador()
        resultado['consistencia'] = prop.verificar_consistencia()
    except Exception as e:
        resultado['consistencia'] = {'error': str(e)}

    return {"status": "ok", **resultado}


@app.get("/version")
async def version():
    """Version del sistema y briefings implementados."""
    return {
        "version": VERSION,
        "briefings_implementados": [
            "SN-00: Schema verification",
            "SN-01: Seed matriz",
            "SN-02: Config models",
            "SN-03: Telemetria",
            "SN-04: Gestor basico",
            "SN-05: Mejora continua",
            "SN-06: Registrador PID",
            "SN-07: Gestor GAMC",
            "SN-08: Constraint Manifold (13 reglas)",
            "SN-09: Motor vN SFCE",
            "SN-10: Flywheel + Autopoiesis",
            "SN-11: Reactor vN",
            "SN-12: Gestor Pasos 8-10",
            "SN-13: Sinema",
            "SN-14: Propagacion",
            "SN-15: Exocortex ETL",
            "SN-16: Monitoring + Circuit Breaker",
            "SN-17: Test Suite",
            "SN-18: Integration Dashboard",
        ],
        "componentes": {
            "motor_vn": "SFCE + Dual Process + Sandwich LLM",
            "gestor_gamc": "10 pasos + auto-ajuste segundo orden",
            "registrador_pid": "P/I/D con anti-windup",
            "constraint_manifold": "13 reglas: validar/proyectar/generar",
            "reactor_vn": "Generador de preguntas desde gaps",
            "sinema": "Weakening/Projection/Relaxation",
            "propagador": "Cascade updates cross-table",
            "exocortex_etl": "ETL + multi-tenant",
            "monitoring": "SLOs + Circuit Breaker",
            "scheduler": "Flywheel adaptativo + Autopoiesis",
            "test_suite": "7 invariantes automatizados",
        },
        "patrones_aplicados": 9,
    }


# ==========================================
# SN-10: Flywheel + Autopoiesis Scheduler
# ==========================================

@app.on_event("startup")
async def iniciar_scheduler_gestor():
    """Iniciar scheduler adaptativo del Gestor como background task."""
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler._task = asyncio.create_task(scheduler.loop_infinito(delay_inicial_s=60))
        print("[SN-10] Gestor Scheduler iniciado (primer ciclo en 60s)")
    except Exception as e:
        print(f"[SN-10] Error iniciando scheduler: {e}")


@app.on_event("startup")
async def iniciar_watchdog():
    """Start system watchdog as background task."""
    try:
        from core.watchdog import get_watchdog
        watchdog = get_watchdog()
        watchdog._task = asyncio.create_task(watchdog.loop(delay_inicial_s=120))
        print("[WATCHDOG] System watchdog iniciado (primer check en 120s)")
    except Exception as e:
        print(f"[WATCHDOG] Error iniciando watchdog: {e}")


@app.on_event("shutdown")
async def detener_scheduler_gestor():
    """Detener scheduler y watchdog al apagar la app."""
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.stop()
        print("[SN-10] Gestor Scheduler detenido")
    except Exception:
        pass
    try:
        from core.watchdog import get_watchdog
        get_watchdog().stop()
        print("[WATCHDOG] Watchdog detenido")
    except Exception:
        pass


@app.get("/watchdog/status")
async def watchdog_status():
    """Estado del watchdog de salud del sistema."""
    from core.watchdog import get_watchdog
    return get_watchdog().get_status()


@app.post("/watchdog/check")
async def watchdog_check_now():
    """Ejecutar un health check manual ahora."""
    from core.watchdog import get_watchdog
    w = get_watchdog()
    checks = w.run_checks()
    errors = [c for c in checks if c.status in ("error", "warning")]
    fixes = w.auto_remediate(checks) if errors else []
    routed = w.route_to_codeos(checks) if errors else {"routed": 0}
    return {
        "status": "ok",
        "checks": [c.to_dict() for c in checks],
        "errors": len(errors),
        "auto_fixed": len(fixes),
        "fixes": fixes,
        "routed_to_codeos": routed,
    }


@app.get("/gestor/estado")
async def gestor_estado():
    """Estado completo del scheduler: ultimo loop, proximo, flywheel history."""
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        return {"status": "ok", "estado": scheduler.get_estado()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/flywheel")
async def gestor_flywheel():
    """Metricas de aceleracion compuesta: f(n) y Delta(n) por ciclo."""
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        estado = scheduler.get_estado()
        return {
            "status": "ok",
            "ciclos": estado['ciclos_completados'],
            "flywheel": estado['flywheel'],
            "intervalo_actual_h": estado['intervalo_actual_h'],
            "formula": "f(n+1) = f(n) * (1 + Delta(n))",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/gestor/autopoiesis")
async def gestor_autopoiesis():
    """Estado del ciclo autopoietico (4 checks)."""
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        auto = scheduler.check_autopoiesis()
        return {
            "status": "ok",
            "autopoiesis": auto,
            "descripcion": {
                "check_preguntas": "Hay preguntas activas en la Matriz?",
                "check_gaps": "Los gaps estan decreciendo (24h vs 48h)?",
                "check_tasa": "La tasa de cierre esta subiendo?",
                "check_datapoints": "Los datapoints estan creciendo?",
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/gestor/autopoiesis/reset-alertas")
async def gestor_autopoiesis_reset_alertas():
    """Consumir alertas autopoiesis_roto stale y re-verificar ciclo."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"status": "error", "error": "no_db"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE marcas_estigmergicas
                    SET consumida = true
                    WHERE consumida = false AND tipo = 'alerta'
                      AND contenido->>'tipo' = 'autopoiesis_roto'
                    RETURNING id
                """)
                consumed = cur.fetchall()
            conn.commit()
        finally:
            put_conn(conn)

        from core.gestor_scheduler import get_scheduler
        auto = get_scheduler().check_autopoiesis()
        return {
            "status": "ok",
            "alertas_consumidas": len(consumed),
            "autopoiesis": auto,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ──────────────────────────────────────────────
# SN-19: Information Layer endpoints
# ──────────────────────────────────────────────

@app.post("/info/mutual-information")
async def info_mutual_information(request: Request):
    """Calcular mutual information entre dos textos."""
    try:
        body = await request.json()
        from core.information_layer import mutual_information
        result = mutual_information(body.get('texto_a', ''), body.get('texto_b', ''))
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/info/entropy")
async def info_entropy(request: Request):
    """Calcular Shannon entropy de un texto."""
    try:
        body = await request.json()
        from core.information_layer import shannon_entropy
        h = shannon_entropy(body.get('texto', ''))
        return {"status": "ok", "entropy": h}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/info/bottleneck")
async def info_bottleneck(request: Request):
    """Information Bottleneck: ranking de outputs por contribucion informativa."""
    try:
        body = await request.json()
        from core.information_layer import information_bottleneck
        outputs = body.get('outputs', [])
        result = information_bottleneck(outputs)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/info/redundancia")
async def info_redundancia():
    """Analizar redundancia/complementariedad entre inteligencias (DB)."""
    try:
        from core.information_layer import analizar_inteligencias_db
        result = analizar_inteligencias_db()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ──────────────────────────────────────────────
# SN-20: Criticality Engine endpoints
# ──────────────────────────────────────────────

@app.get("/criticality/temperatura")
async def criticality_temperatura():
    """Temperatura del sistema (borde del caos)."""
    try:
        from core.criticality_engine import get_criticality_engine
        engine = get_criticality_engine()
        result = engine.calcular_temperatura()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/criticality/avalanchas")
async def criticality_avalanchas():
    """Distribucion de avalanchas (SOC)."""
    try:
        from core.criticality_engine import get_criticality_engine
        engine = get_criticality_engine()
        result = engine.medir_avalanchas()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/criticality/transiciones")
async def criticality_transiciones():
    """Transiciones de fase detectadas."""
    try:
        from core.criticality_engine import get_criticality_engine
        engine = get_criticality_engine()
        result = engine.detectar_transiciones_fase()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/criticality/estado")
async def criticality_estado():
    """Estado completo del motor de criticalidad."""
    try:
        from core.criticality_engine import get_criticality_engine
        engine = get_criticality_engine()
        result = engine.get_estado_completo()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ──────────────────────────────────────────────
# SN-21: Metacognitive Layer endpoints
# ──────────────────────────────────────────────

@app.post("/metacognitive/fok")
async def metacognitive_fok(request: Request):
    """Feeling of Knowing: estimar confianza ANTES de ejecutar."""
    try:
        body = await request.json()
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        input_texto = body.get('input', body.get('query', ''))
        result = meta.feeling_of_knowing(
            input_texto=input_texto,
            celda=body.get('celda', 'ConservarxSalud'),
            programa=body.get('programa'),
        )
        return {"status": "ok", "confianza": result.get('fok'), **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/metacognitive/reset-kalman")
async def metacognitive_reset_kalman():
    """Reset Kalman estimators tras recalibración de señales (Fase 3)."""
    try:
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        meta.reset_kalman()
        return {"status": "ok", "message": "Kalman reset. Se recalibrará con nuevos datos."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/metacognitive/jol")
async def metacognitive_jol(request: Request):
    """Judgment of Learning: evaluar calidad DESPUES de ejecutar."""
    try:
        body = await request.json()
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        result = meta.judgment_of_learning(resultado=body.get('resultado', {}))
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/metacognitive/emergencia")
async def metacognitive_emergencia(request: Request):
    """Detectar insights emergentes (todo > suma de partes)."""
    try:
        body = await request.json()
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        result = meta.detectar_emergencia(
            outputs=body.get('outputs', []),
            resultado_integrado=body.get('resultado_integrado', {}),
        )
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/metacognitive/kalman")
async def metacognitive_kalman():
    """Estado de estimadores Kalman por celda."""
    try:
        from core.metacognitive import get_metacognitive
        meta = get_metacognitive()
        result = meta.get_kalman_estado()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ──────────────────────────────────────────────
# SN-22: Predictive Controller endpoints
# ──────────────────────────────────────────────

@app.get("/predictive/trayectoria")
async def predictive_trayectoria():
    """Predecir trayectoria de tasa_cierre (MPC)."""
    try:
        from core.predictive_controller import get_predictive_controller
        ctrl = get_predictive_controller()
        result = ctrl.predecir_trayectoria()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/predictive/plan")
async def predictive_plan():
    """Plan de acciones optimas para proximos N ciclos."""
    try:
        from core.predictive_controller import get_predictive_controller
        ctrl = get_predictive_controller()
        result = ctrl.planificar_acciones()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/predictive/atractores")
async def predictive_atractores():
    """Paisaje de atractores (clusters de problemas)."""
    try:
        from core.predictive_controller import get_predictive_controller
        ctrl = get_predictive_controller()
        result = ctrl.landscape.detectar_atractores()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/predictive/estado")
async def predictive_estado():
    """Estado completo del controlador predictivo."""
    try:
        from core.predictive_controller import get_predictive_controller
        ctrl = get_predictive_controller()
        result = ctrl.get_estado_completo()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ──────────────────────────────────────────────
# SN-23: Game Theory Engine endpoints
# ──────────────────────────────────────────────

@app.post("/game-theory/analizar")
async def game_theory_analizar(request: Request):
    """Analisis game-theoretic de una composicion de outputs."""
    try:
        body = await request.json()
        from core.game_theory import get_game_theory
        gt = get_game_theory()
        result = gt.analizar_composicion(outputs=body.get('outputs', []))
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/game-theory/incentivos")
async def game_theory_incentivos():
    """Analisis de incentivos: cooperacion vs competencia entre INTs."""
    try:
        from core.game_theory import get_game_theory
        gt = get_game_theory()
        result = gt.mechanism.analizar_incentivos()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/game-theory/equilibrios")
async def game_theory_equilibrios():
    """Nash equilibria: combinaciones estables de INTs."""
    try:
        from core.game_theory import get_game_theory
        gt = get_game_theory()
        result = gt.mechanism.detectar_equilibrios()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/game-theory/estado")
async def game_theory_estado():
    """Estado completo del motor game-theoretic."""
    try:
        from core.game_theory import get_game_theory
        gt = get_game_theory()
        result = gt.get_estado_completo()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# CEO Advisor — Self-Driving Intelligence
# ==========================================

@app.get("/ceo/advisor")
async def ceo_advisor():
    """Scan all subsystems and return prioritized actions for the CEO."""
    try:
        from core.system_advisor import get_advisor
        advisor = get_advisor()
        result = advisor.scan_system()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/ceo/advisor/execute")
async def ceo_advisor_execute(request: Request):
    """Execute a recommended action.

    Body: {"accion": "POST /gestor/loop"}
    """
    try:
        body = await request.json()
        accion = body.get('accion', '')
        if not accion:
            return {"status": "error", "error": "accion requerida"}
        from core.system_advisor import get_advisor
        advisor = get_advisor()
        result = advisor.execute_action(accion)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/ceo/advisor/capabilities")
async def ceo_advisor_capabilities():
    """List all system capabilities with usage status."""
    try:
        from core.system_advisor import get_advisor
        advisor = get_advisor()
        result = advisor.get_capabilities()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# Control Financiero
# ==========================================

@app.get("/costes/resumen")
async def costes_resumen(consumidor: str = None, meses: int = 3):
    """Resumen completo de costes: por modelo, consumidor, componente."""
    try:
        from core.costes import resumen_costes
        return resumen_costes(consumidor=consumidor, meses=meses)
    except Exception as e:
        return {"error": str(e)}


@app.get("/costes/por-modelo")
async def costes_por_modelo():
    """Costes desglosados por modelo LLM y mes."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "no_db"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM costes_por_modelo_mes")
            cols = ['modelo', 'mes', 'llamadas', 'tokens_in', 'tokens_out',
                    'coste_total', 'coste_medio', 'latencia_ms']
            return {"costes": [
                dict(zip(cols, [r[0], str(r[1])[:7]] + list(r[2:])))
                for r in cur.fetchall()
            ]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


@app.get("/costes/por-consumidor")
async def costes_por_consumidor():
    """Costes desglosados por exocortex/consumidor y mes."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "no_db"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM costes_por_consumidor_mes")
            cols = ['consumidor', 'mes', 'llamadas', 'coste_total', 'coste_medio', 'modelos']
            return {"costes": [
                dict(zip(cols, [r[0], str(r[1])[:7]] + list(r[2:])))
                for r in cur.fetchall()
            ]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


@app.get("/costes/presupuestos")
async def costes_presupuestos():
    """Estado de presupuestos por consumidor."""
    try:
        from core.costes import resumen_costes
        r = resumen_costes(meses=1)
        return {"presupuestos": r.get('presupuestos', [])}
    except Exception as e:
        return {"error": str(e)}


@app.post("/costes/presupuesto")
async def set_presupuesto(request: Request):
    """Crear o actualizar presupuesto de un consumidor."""
    body = await request.json()
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "no_db"}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO presupuestos (consumidor, limite_mensual_usd, alerta_al_pct)
                VALUES (%s, %s, %s)
                ON CONFLICT (consumidor) DO UPDATE SET
                    limite_mensual_usd = EXCLUDED.limite_mensual_usd,
                    alerta_al_pct = EXCLUDED.alerta_al_pct,
                    updated_at = now()
            """, [body['consumidor'], body['limite'], body.get('alerta_pct', 80)])
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


@app.get("/costes/proyeccion")
async def costes_proyeccion():
    """Proyeccion de costes basada en uso actual."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "no_db"}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM costes_resumen_30d")
            row = cur.fetchone()
            if not row or row[0] == 0:
                return {"proyeccion": "sin datos"}
            return {
                "total_llamadas": row[0],
                "coste_total_30d": float(row[3]) if row[3] else 0,
                "coste_medio_diario": float(row[4]) if row[4] else 0,
                "proyeccion_mensual": float(row[5]) if row[5] else 0,
            }
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


# ==========================================
# CEO Copiloto
# ==========================================

@app.post("/ceo/copiloto")
async def ceo_copiloto(request: Request):
    """Copiloto del CEO: explica el estado del sistema en lenguaje humano."""
    body = await request.json()
    seccion = body.get('seccion', 'resumen')
    pregunta = body.get('pregunta', '')
    historial = body.get('historial', [])

    # 1. Recoger datos reales del sistema
    datos_sistema = _recoger_datos_copiloto(seccion)

    # 2. Generar explicacion via LLM
    from core.api import call_openrouter, extract_response
    from core.costes import set_call_context
    set_call_context(componente='copiloto_ceo', operacion='explicacion')

    prompt = _construir_prompt_copiloto(seccion, datos_sistema, pregunta, historial)

    try:
        response = call_openrouter(
            messages=[{"role": "user", "content": prompt}],
            model='xiaomi/mimo-v2-flash',
            max_tokens=1000,
            temperature=0.3,
        )
        texto, _, _ = extract_response(response)
    except Exception as e:
        texto = f"Error al generar explicacion: {e}"

    # 3. Parsear respuesta
    resultado = _parsear_respuesta_copiloto(texto)

    # 4. Registrar interaccion
    try:
        from core.telemetria import registrar_metrica
        registrar_metrica('copiloto', 'interaccion', {
            'seccion': seccion,
            'pregunta': pregunta[:200] if pregunta else None,
            'acciones_sugeridas': len(resultado.get('acciones', [])),
        })
    except Exception:
        pass

    return resultado


@app.post("/ceo/copiloto/feedback")
async def copiloto_feedback(request: Request):
    """Feedback del usuario sobre explicaciones del copiloto."""
    body = await request.json()
    try:
        from core.telemetria import registrar_metrica
        registrar_metrica('copiloto', 'feedback', {
            'tipo': body.get('tipo'),
            'seccion': body.get('seccion'),
        })
    except Exception:
        pass
    return {"status": "ok"}


def _recoger_datos_copiloto(seccion: str) -> dict:
    """Recoge datos relevantes del sistema segun la seccion."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "sin conexion"}

    datos = {}
    try:
        with conn.cursor() as cur:
            # Siempre: estado general
            cur.execute("SELECT COUNT(*) FROM datapoints_efectividad WHERE calibrado = true")
            datos['total_casos_calibrados'] = cur.fetchone()[0]

            cur.execute("""
                SELECT celda_objetivo, COUNT(*) as n,
                       ROUND(AVG(1.0 - gap_post/NULLIF(gap_pre, 0))::numeric, 2) as tasa_media
                FROM datapoints_efectividad
                WHERE calibrado = true AND gap_pre > 0
                GROUP BY celda_objetivo
                ORDER BY tasa_media DESC
            """)
            datos['celdas'] = [{'celda': r[0], 'n': r[1], 'tasa': float(r[2])} for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) FROM programas_compilados WHERE activo = true")
            datos['programas_usados'] = cur.fetchone()[0]

            if seccion in ('resumen', 'decisiones', 'costes'):
                # Senales pendientes
                cur.execute("SELECT COUNT(*) FROM señales WHERE resuelta = false")
                datos['señales_pendientes'] = cur.fetchone()[0]

                # Marcas sin consumir
                cur.execute("SELECT COUNT(*) FROM marcas_estigmergicas WHERE consumida = false")
                datos['marcas_pendientes'] = cur.fetchone()[0]

                # Mejor y peor celda
                if datos['celdas']:
                    datos['mejor_celda'] = datos['celdas'][0]
                    datos['peor_celda'] = datos['celdas'][-1] if len(datos['celdas']) > 1 else None

            if seccion == 'costes':
                try:
                    from core.costes import resumen_costes
                    datos['costes'] = resumen_costes(meses=1)
                except Exception:
                    datos['costes'] = None

            if seccion == 'guia':
                datos['pestañas'] = [
                    {'nombre': 'Advisor', 'que_hace': 'Escanea todo el sistema y recomienda acciones'},
                    {'nombre': 'Metrics', 'que_hace': 'Rendimiento: latencia, costes, errores'},
                    {'nombre': 'Models', 'que_hace': 'Modelos de IA activos y su rendimiento'},
                    {'nombre': 'Neural', 'que_hace': 'Base de conocimiento: patrones e informacion'},
                    {'nombre': 'Flywheel', 'que_hace': 'Indicador de aprendizaje del sistema'},
                    {'nombre': 'Costes', 'que_hace': 'Cuanto gastas en IA por modelo y exocortex'},
                ]

        return datos
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


def _construir_prompt_copiloto(seccion: str, datos: dict, pregunta: str, historial: list) -> str:
    """Construye el prompt para el LLM copiloto."""
    import json as _json

    contexto_historial = ""
    if historial:
        contexto_historial = "\nUltimas interacciones:\n"
        for h in historial[-3:]:
            contexto_historial += f"- Usuario: {h.get('pregunta', '')}\n- Copiloto: {h.get('respuesta', '')[:100]}...\n"

    mejor = datos.get('mejor_celda', {})
    peor = datos.get('peor_celda', {})

    TRADUCCIONES = {
        'CaptarxSalud': 'como captas clientes e ingresos',
        'ConservarxSalud': 'como mantienes lo que funciona en tu negocio',
        'DepurarxSalud': 'que deberiaz eliminar del negocio',
        'DistribuirxSalud': 'como repartes tu tiempo y recursos',
        'FronteraxSalud': 'donde pones los limites del negocio',
        'AdaptarxSalud': 'como te adaptas a cambios',
        'ReplicarxSalud': 'como podrías escalar o copiar tu modelo',
        'CaptarxSentido': 'por que la gente elige tu negocio',
        'ConservarxSentido': 'que le da sentido a tu negocio',
        'FronteraxSentido': 'que NO es tu negocio',
        'AdaptarxSentido': 'como evoluciona tu proposito',
        'ReplicarxSentido': 'si tu negocio tiene sentido sin ti',
        'CaptarxContinuidad': 'de donde vendran los ingresos en 3 anos',
        'ConservarxContinuidad': 'que necesitas proteger para sobrevivir',
        'DepurarxContinuidad': 'que te esta frenando a largo plazo',
        'FronteraxContinuidad': 'hasta donde llegaras',
        'AdaptarxContinuidad': 'como cambiarás cuando sea necesario',
        'ReplicarxContinuidad': 'puedes escalar sin romperte',
        'DistribuirxSentido': 'a que le dedicas tu energia',
        'DistribuirxContinuidad': 'como asignas recursos para el futuro',
        'DepurarxSentido': 'que sobra y no aporta sentido',
    }

    def traducir_celda(c):
        return TRADUCCIONES.get(c, c)

    prompts = {
        'resumen': f"""Eres el copiloto de un sistema de analisis de negocios. Hablas con Jesus, un empresario. NO uses jerga tecnica.

Datos del sistema:
- Casos analizados: {datos.get('total_casos_calibrados', 0)}
- Mejor area: {traducir_celda(mejor.get('celda', '?'))} (acierta {mejor.get('tasa', 0):.0%} de las veces)
- Peor area: {traducir_celda(peor.get('celda', '?'))} (acierta {peor.get('tasa', 0):.0%} de las veces)
- Senales pendientes: {datos.get('señales_pendientes', 0)}
{contexto_historial}
{f'Jesus pregunta: {pregunta}' if pregunta else ''}

Responde con:
1. EXPLICACION: Un parrafo corto explicando el estado. Traduce nombres tecnicos a lenguaje de negocio.
2. ACCIONES: 1-3 acciones concretas. Formato: - texto de la accion
3. SIGUIENTE: Que deberia mirar despues.

Se directo. No adules. Interpreta los datos.""",

        'decisiones': f"""Eres el copiloto de un sistema de analisis de negocios. Jesus necesita tomar decisiones. NO uses jerga tecnica.

Areas analizadas (de mejor a peor):
{chr(10).join(f"- {traducir_celda(c['celda'])}: {c['tasa']:.0%} acierto en {c['n']} analisis" for c in datos.get('celdas', [])[:8])}
- Senales sin resolver: {datos.get('señales_pendientes', 0)}
- Marcas pendientes: {datos.get('marcas_pendientes', 0)}
{contexto_historial}
{f'Jesus pregunta: {pregunta}' if pregunta else ''}

Presenta decisiones como consultor:
1. EXPLICACION: Que decisiones hay que tomar y por que
2. ACCIONES: Opciones concretas
3. SIGUIENTE: Siguiente paso""",

        'guia': f"""Eres el copiloto de un sistema de analisis de negocios. Jesus quiere entender el dashboard. NO uses jerga tecnica.

Pestanas disponibles:
{chr(10).join(f"- {p['nombre']}: {p['que_hace']}" for p in datos.get('pestañas', []))}

Estado: {datos.get('total_casos_calibrados', 0)} casos analizados.
{contexto_historial}
{f'Jesus pregunta: {pregunta}' if pregunta else ''}

Responde con:
1. EXPLICACION: Que es cada pestana en lenguaje simple
2. ACCIONES: Por donde empezar
3. SIGUIENTE: Que ignorar de momento""",

        'costes': f"""Eres el copiloto financiero de un sistema de analisis de negocios. Jesus quiere entender cuanto cuesta operar el sistema.

Datos financieros:
{_json.dumps(datos.get('costes', {}), indent=2, default=str)[:2000]}

Explica en euros (1 USD = 0.92 EUR):
1. EXPLICACION: Cuanto se ha gastado y en que. Di "el modelo que analiza tus casos" en vez de nombres tecnicos.
2. ACCIONES: Si algo gasta demasiado, sugiere alternativas
3. SIGUIENTE: Que vigilar""",
    }

    if seccion not in prompts:
        return f"""Eres el copiloto de un sistema de analisis de negocios. Jesus esta mirando la pestana '{seccion}'. NO uses jerga tecnica.

Datos: {_json.dumps(datos, indent=2, default=str)[:2000]}
{contexto_historial}
{f'Jesus pregunta: {pregunta}' if pregunta else ''}

1. EXPLICACION: que ve y que significa
2. ACCIONES: que hacer (1-2 acciones)
3. SIGUIENTE: que mirar despues"""

    return prompts[seccion]


def _parsear_respuesta_copiloto(texto: str) -> dict:
    """Parsea la respuesta del LLM en estructura util."""
    resultado = {
        'explicacion': '',
        'acciones': [],
        'siguiente': '',
    }

    lines = texto.strip().split('\n')
    seccion_actual = 'explicacion'
    buffer = []

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if line_lower.startswith('explicaci') or line_lower.startswith('1.'):
            if buffer and seccion_actual == 'explicacion':
                resultado['explicacion'] = '\n'.join(buffer).strip()
            content = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else ''
            buffer = [content] if content else []
            seccion_actual = 'explicacion'
        elif line_lower.startswith('accion') or line_lower.startswith('2.'):
            if buffer and seccion_actual == 'explicacion':
                resultado['explicacion'] = '\n'.join(buffer).strip()
            buffer = []
            seccion_actual = 'acciones'
        elif line_lower.startswith('siguiente') or line_lower.startswith('3.'):
            if buffer and seccion_actual == 'explicacion' and not resultado['explicacion']:
                resultado['explicacion'] = '\n'.join(buffer).strip()
            content = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else line_stripped
            resultado['siguiente'] = content
            seccion_actual = 'siguiente'
            buffer = []
        elif seccion_actual == 'acciones' and line_stripped.startswith(('-', '*', '•')):
            resultado['acciones'].append({
                'texto': line_stripped.lstrip('-*• ').strip(),
                'endpoint': None,
                'auto_ejecutable': False,
            })
        else:
            buffer.append(line)

    if buffer and not resultado['explicacion']:
        resultado['explicacion'] = '\n'.join(buffer).strip()

    if not resultado['explicacion']:
        resultado['explicacion'] = texto.strip()

    return resultado


# ============================================================
# STEP 15: Chief API endpoints
# ============================================================

@app.post("/chief/execute")
async def chief_execute(request: Request):
    """Execute Chief design flow — SSE stream."""
    body = await request.json()
    domain = body.get("domain", "")
    focus = body.get("focus")
    verify_tier = body.get("verify_tier", "standard")

    if not domain:
        raise HTTPException(400, "domain is required")

    async def stream():
        try:
            from core.chief import Chief, ChiefConversation
            chief = Chief()
            conv = ChiefConversation(chief)

            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing domain...'})}\n\n"

            # Initial analysis
            result = conv.process_message(domain)
            yield f"data: {json.dumps({'type': 'analysis', 'data': result})}\n\n"

            # If focus provided, continue
            if focus and conv.state != "done":
                yield f"data: {json.dumps({'type': 'status', 'message': f'Designing with focus: {focus}...'})}\n\n"
                result = conv.process_message(focus)
                yield f"data: {json.dumps({'type': 'design_result', 'data': result}, default=str)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'state': conv.state})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/chief/status/{consumidor}")
async def chief_status(consumidor: str):
    """Get domain status via Chief."""
    try:
        from core.chief import Chief
        chief = Chief()
        return chief.get_domain_status(consumidor)
    except Exception as e:
        return {"error": str(e)}


@app.get("/chief/suggest/{consumidor}")
async def chief_suggest(consumidor: str):
    """Suggest next step for an exocortex."""
    try:
        from core.chief import Chief
        chief = Chief()
        return chief.suggest_next_step(consumidor)
    except Exception as e:
        return {"error": str(e)}


@app.get("/chief/designs")
async def chief_designs():
    """List recent designs from design_registry."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {"designs": []}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, consumidor, domain, focus, status,
                           total_cost_usd, created_at
                    FROM design_registry
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
                return {
                    "designs": [
                        {
                            "id": str(r[0]),
                            "consumidor": r[1],
                            "domain": r[2],
                            "focus": r[3],
                            "status": r[4],
                            "cost": r[5],
                            "created_at": r[6].isoformat() if r[6] else None,
                        }
                        for r in cur.fetchall()
                    ]
                }
        finally:
            put_conn(conn)
    except Exception as e:
        return {"designs": [], "error": str(e)}


# ============================================================
# STEP 19: Self-healing API endpoints
# ============================================================

@app.get("/self-healing/status")
async def self_healing_status():
    """Self-healing system status: last cycle info and summary."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        queue = sh.get_queue()
        return {
            "status": "active",
            "pending_count": len(queue),
            "last_cycle": getattr(sh, 'last_cycle', None),
            "fontaneria_ejecutadas": getattr(sh, 'fontaneria_count', 0),
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@app.get("/self-healing/pending")
async def self_healing_pending():
    """Get pending improvements (alias for /self-healing/queue with enriched data)."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        queue = sh.get_queue()
        return {"improvements": queue, "count": len(queue)}
    except Exception as e:
        return {"improvements": [], "count": 0, "error": str(e)}


@app.post("/self-healing/run")
async def self_healing_run():
    """Run one self-healing cycle."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        result = sh.run_cycle()
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/self-healing/queue")
async def self_healing_queue():
    """Get pending architectural improvements queue."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        return {"queue": sh.get_queue()}
    except Exception as e:
        return {"queue": [], "error": str(e)}


@app.post("/self-healing/approve/{improvement_id}")
async def self_healing_approve(improvement_id: str):
    """CEO approves an architectural improvement."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        return sh.approve_improvement(improvement_id)
    except Exception as e:
        return {"error": str(e)}


@app.post("/self-healing/reject/{improvement_id}")
async def self_healing_reject(improvement_id: str):
    """CEO rejects an architectural improvement."""
    try:
        from core.self_healing import get_self_healing
        sh = get_self_healing()
        return sh.reject_improvement(improvement_id)
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
# B3: Matriz 3L x 7F endpoints
# ──────────────────────────────────────────────

@app.get("/matriz/estado")
async def matriz_estado():
    """Estado completo de la Matriz 3Lx7F: 21 celdas + resumen por lente/funcion + top gaps."""
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 21 celdas
            cur.execute("SELECT * FROM celdas_matriz ORDER BY funcion, lente")
            celdas = cur.fetchall()

            # Por lente (3 rows)
            cur.execute("SELECT * FROM matriz_por_lente")
            por_lente = cur.fetchall()

            # Por funcion (7 rows)
            cur.execute("SELECT * FROM matriz_por_funcion")
            por_funcion = cur.fetchall()

            # Top 5 gaps
            cur.execute("""
                SELECT id, lente, funcion, gap, grado_actual, n_datapoints
                FROM celdas_matriz
                ORDER BY gap DESC
                LIMIT 5
            """)
            top_gaps = cur.fetchall()

        return {
            "celdas": celdas,
            "por_lente": por_lente,
            "por_funcion": por_funcion,
            "top_gaps": top_gaps,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


@app.get("/matriz/termometro")
async def matriz_termometro(consumidor: str = ""):
    """Termometro de la Matriz: 21 celdas con color (rojo/naranja/amarillo/verde).

    Sin consumidor: lee vista matriz_completa (sistema).
    Con consumidor: LEFT JOIN datapoints por consumidor, recalcula gap/color per-consumer.
    """
    from core.db_pool import get_conn, put_conn
    conn = get_conn()
    if not conn:
        return {"error": "No DB"}
    try:
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if not consumidor:
                # Sistema: vista precalculada
                cur.execute("SELECT * FROM matriz_completa")
                celdas = cur.fetchall()
            else:
                # Per-consumer: recalcular gap/color
                cur.execute("""
                    SELECT
                        cm.id, cm.lente, cm.funcion,
                        cm.grado_actual AS grado_actual_sistema,
                        cm.grado_objetivo, cm.gap AS gap_sistema,
                        COALESCE(dp.n, 0) AS n_datapoints_consumidor,
                        COALESCE(dp.avg_gap_post, cm.gap) AS gap,
                        CASE
                            WHEN COALESCE(dp.avg_gap_post, cm.gap) >= 0.6 THEN 'rojo'
                            WHEN COALESCE(dp.avg_gap_post, cm.gap) >= 0.3 THEN 'naranja'
                            WHEN COALESCE(dp.avg_gap_post, cm.gap) >= 0.1 THEN 'amarillo'
                            ELSE 'verde'
                        END AS color_termometro
                    FROM celdas_matriz cm
                    LEFT JOIN (
                        SELECT celda_objetivo,
                               COUNT(*) AS n,
                               AVG(gap_post) AS avg_gap_post
                        FROM datapoints_efectividad
                        WHERE consumidor = %s
                          AND celda_objetivo IS NOT NULL
                        GROUP BY celda_objetivo
                    ) dp ON dp.celda_objetivo = cm.id
                    ORDER BY cm.funcion, cm.lente
                """, [consumidor])
                celdas = cur.fetchall()

        return {
            "consumidor": consumidor or "sistema",
            "celdas": celdas,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        put_conn(conn)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
