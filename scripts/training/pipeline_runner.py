#!/usr/bin/env python3
"""
OMNI-MIND Pipeline Runner — Orquestador automático de entrenamiento
===================================================================
Ejecuta el pipeline completo de entrenamiento del Simbionte de forma
automatizada, como lo hacen labs tipo Anthropic/Meta/DeepMind.

Pipeline:
  Pre-flight -> Labeling (con aprobacion CEO) -> Training -> Eval -> Diagnostico -> Iteracion

Automatizacion:
  - 80% corre sin intervencion humana
  - CostGate para operaciones > $5 (Telegram al CEO, espera respuesta)
  - Quality gates automaticos entre cada paso
  - Auto-fixes cuando un gate falla
  - Maximo 3 iteraciones sin mejora -> para (Patron 7)
  - Registro en experiment_manager + Telegram en cada transicion

Uso:
  python3 pipeline_runner.py                    # Ejecuta pipeline completo desde donde este
  python3 pipeline_runner.py --from train       # Empieza desde el paso de training
  python3 pipeline_runner.py --step data_audit  # Ejecuta solo un paso
  python3 pipeline_runner.py --status           # Muestra estado del pipeline
  python3 pipeline_runner.py --dry-run          # Muestra que haria sin ejecutar
  python3 pipeline_runner.py --reset            # Resetea estado del pipeline
"""

import os
import sys
import json
import time
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Rutas absolutas (obligatorio — agent threads resetean cwd) ──
ROOT = Path(__file__).resolve().parents[2]       # motor-semantico/
PROJECT_ROOT = ROOT.parent                        # omni-mind-cerebro/
SCRIPTS_DIR = ROOT / "scripts" / "training"
EXPERIMENTS_DIR = ROOT / "experiments"
MANAGER_SCRIPT = ROOT / "scripts" / "experiment_manager" / "manager.py"
AUTO_FIXES_SCRIPT = SCRIPTS_DIR / "auto_fixes.py"
PIPELINE_STATE_FILE = EXPERIMENTS_DIR / "pipeline_state.json"

# Importar shared_config para Telegram y credenciales
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from shared_config import config as _cfg
    TELEGRAM_TOKEN = getattr(_cfg, "TELEGRAM_TOKEN", None)
    TELEGRAM_CHAT_ID = getattr(_cfg, "TELEGRAM_CHAT_ID", "8091188679")
except ImportError:
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = "8091188679"


# ═══════════════════════════════════════════════════════════════
# PIPELINE DEFINITION
# ═══════════════════════════════════════════════════════════════

PIPELINE_STEPS = [

    # ── Pre-flight ($0) ──────────────────────────────────────────
    {
        "id": "verify_infra",
        "name": "Verificar infraestructura ML",
        "phase": "pre-flight",
        "script": "verify_infra.py",
        "gate": {"type": "exit_code", "expect": 0},
        "cost": 0,
        "auto": True,
    },
    {
        "id": "data_audit",
        "name": "Auditoria de datos gold set",
        "phase": "pre-flight",
        "script": "data_audit.py",
        "gate": {"type": "exit_code", "expect": 0},
        "cost": 0,
        "auto": True,
    },

    # ── Labeling (requiere aprobacion CEO) ───────────────────────
    {
        "id": "poc_micro",
        "name": "POC micro 50 textos x 443 dims",
        "phase": "labeling",
        "script": "label_poc_micro.py",
        "gate": {"type": "metric", "metric": "iaa", "operator": ">=", "threshold": 0.70},
        "cost_gate": True,
        "estimated_cost": 3.0,
        "auto": False,  # Requiere aprobacion CEO
    },
    {
        "id": "filter_dims",
        "name": "Filtrar dims por varianza y correlacion",
        "phase": "labeling",
        "script": "filter_dims.py",
        "gate": {"type": "metric", "metric": "surviving_dims", "operator": ">=", "threshold": 300},
        "cost": 0,
        "auto": True,
    },
    {
        "id": "gold_set_v3",
        "name": "Gold set 500 textos x dims supervivientes",
        "phase": "labeling",
        "script": "label_gold_set_v3.py",
        "gate": {"type": "metric", "metric": "n_labeled", "operator": ">=", "threshold": 450},
        "cost_gate": True,
        "estimated_cost": 80.0,
        "auto": False,  # Requiere aprobacion CEO
    },

    # ── Training ($0, GPU local) ─────────────────────────────────
    {
        "id": "train_baseline",
        "name": "Train Arquitectura A (baseline CLS)",
        "phase": "training",
        "script": "train.py",
        "args": ["--arch", "baseline", "--experiment", "simbionte_arch_a"],
        "gate": {"type": "metric", "metric": "corr_global", "operator": ">", "threshold": 0.10},
        "cost": 0,
        "auto": True,
    },
    {
        "id": "train_pooling",
        "name": "Train Arquitectura B (weighted pooling)",
        "phase": "training",
        "script": "train.py",
        "args": ["--arch", "pooling", "--experiment", "simbionte_arch_b"],
        "gate": {"type": "metric", "metric": "corr_global", "operator": ">", "threshold": 0.10},
        "cost": 0,
        "auto": True,
    },
    {
        "id": "train_layer_heads",
        "name": "Train Arquitectura C (layer-specific heads)",
        "phase": "training",
        "script": "train.py",
        "args": ["--arch", "layer_heads", "--experiment", "simbionte_arch_c"],
        "gate": {"type": "metric", "metric": "corr_global", "operator": ">", "threshold": 0.10},
        "cost": 0,
        "auto": True,
    },

    # ── Eval ($0) ────────────────────────────────────────────────
    {
        "id": "eval_ablation",
        "name": "Comparar 3 arquitecturas (ablacion)",
        "phase": "eval",
        "script": "eval_ablation.py",
        "gate": {"type": "metric", "metric": "best_corr_global", "operator": ">", "threshold": 0.35},
        "cost": 0,
        "auto": True,
    },
    {
        "id": "diagnose",
        "name": "Diagnostico per-dim (las 10 peores)",
        "phase": "eval",
        "script": "diagnose_dims.py",
        "gate": {"type": "metric", "metric": "actionable_fixes", "operator": ">", "threshold": 0},
        "cost": 0,
        "auto": True,
        "on_fail": "auto_fix",  # Si el gate falla, intentar auto-fix
    },

    # ── Iteracion ────────────────────────────────────────────────
    {
        "id": "iterate",
        "name": "Aplicar fixes y re-entrenar",
        "phase": "iteration",
        "script": "iterate.py",
        "gate": {"type": "metric", "metric": "corr_improvement", "operator": ">", "threshold": 0.01},
        "cost": 0,
        "auto": True,
        "max_iterations": 3,  # Patron 7: 3 sin mejora -> parar
    },
]


# ═══════════════════════════════════════════════════════════════
# PIPELINE RUNNER
# ═══════════════════════════════════════════════════════════════

class PipelineRunner:
    """Orquestador del pipeline de entrenamiento del Simbionte."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.state = self._load_state()

    # ── State ──────────────────────────────────────────────────

    def _load_state(self) -> dict:
        """Carga estado persistente del pipeline desde JSON."""
        if PIPELINE_STATE_FILE.exists():
            try:
                with open(PIPELINE_STATE_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("[pipeline] Warning: estado corrupto, reseteando.")
        return {
            "current_step": None,
            "completed_steps": [],
            "failed_steps": [],
            "iteration_count": 0,
            "started_at": None,
            "last_updated": None,
            "metrics": {},
        }

    def _save_state(self):
        """Persiste estado del pipeline a JSON."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(PIPELINE_STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    # ── Telegram ───────────────────────────────────────────────

    def _notify(self, message: str, urgent: bool = False):
        """Envia notificacion por Telegram. Si no hay token, imprime en consola."""
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            prefix = "[URGENT]" if urgent else "[NOTIFY]"
            print(f"{prefix} {message}")
            return

        prefix = "ALERTA" if urgent else "Pipeline"
        text = f"*{prefix} Simbionte*\n{message}"

        try:
            import urllib.request
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = json.dumps({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            }).encode()
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            print(f"[telegram] Error: {e}")
            # Fallback: imprimir igual
            print(f"[NOTIFY] {message}")

    def _wait_ceo_approval(self, step: dict, estimated_cost: float) -> bool:
        """
        Solicita aprobacion al CEO via Telegram y espera respuesta.
        Soporta dos modos:
          - Interactivo: input de stdin
          - Automatico (cron): poll de archivo pending_approval.json

        Retorna True si aprobado, False si rechazado o timeout.
        """
        approval_file = EXPERIMENTS_DIR / "pending_approval.json"

        msg = (
            f"Aprobacion requerida\n"
            f"Paso: `{step['name']}`\n"
            f"Coste estimado: ${estimated_cost:.2f} [SUPOSICION — ejecutar CostGate para coste real]\n\n"
            f"Para aprobar: edita {approval_file} con status='approved'\n"
            f"Para rechazar: status='rejected'"
        )
        self._notify(msg, urgent=True)

        # Escribir archivo de aprobacion pendiente
        approval = {
            "step_id": step["id"],
            "step_name": step["name"],
            "estimated_cost": estimated_cost,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }
        with open(approval_file, "w") as f:
            json.dump(approval, f, indent=2)

        print(f"\n{'='*60}")
        print(f"ESPERANDO APROBACION CEO: {step['name']}")
        print(f"  Coste estimado: ${estimated_cost:.2f}")
        print(f"  Archivo de aprobacion: {approval_file}")
        print(f"  O escribe 'si' / 'no' en stdin.")
        print(f"{'='*60}\n")

        # Poll: stdin (interactivo) o archivo (automatico/cron)
        max_wait_seconds = 3600  # 1 hora max
        start_wait = time.time()

        while True:
            # Check archivo de aprobacion
            if approval_file.exists():
                try:
                    with open(approval_file) as f:
                        data = json.load(f)
                    status = data.get("status", "pending")
                    if status == "approved":
                        print("Aprobado por CEO (via archivo).")
                        approval_file.unlink(missing_ok=True)
                        return True
                    elif status == "rejected":
                        print("Rechazado por CEO (via archivo).")
                        approval_file.unlink(missing_ok=True)
                        return False
                except (json.JSONDecodeError, IOError):
                    pass

            # Check timeout
            if time.time() - start_wait > max_wait_seconds:
                print(f"TIMEOUT: Sin respuesta del CEO en {max_wait_seconds}s. Saltando paso.")
                approval_file.unlink(missing_ok=True)
                return False

            # Check stdin (no bloqueante en modo cron cuando EOF)
            try:
                response = input("Aprobar? (si/no): ").strip().lower()
                if response in ("si", "si", "s", "yes", "y"):
                    approval_file.unlink(missing_ok=True)
                    return True
                elif response in ("no", "n"):
                    approval_file.unlink(missing_ok=True)
                    return False
                else:
                    print("Responde 'si' o 'no'.")
            except EOFError:
                # Sin stdin (modo cron/daemon) — poll archivo cada 10s
                time.sleep(10)

    # ── Experiment Manager ──────────────────────────────────────

    def _manager(self, action: str, name: str, **kwargs):
        """
        Ejecuta una accion del experiment manager.
        Firma exacta del manager:
          create <name> --hypothesis <str>
          start  <name>
          log    <name> --metric k=v [--metric k2=v2] [--note <str>]
          finish <name> --result <str> --decision <str>
        """
        if not MANAGER_SCRIPT.exists():
            print(f"[manager] Script no encontrado: {MANAGER_SCRIPT}")
            return

        cmd = ["python3", str(MANAGER_SCRIPT), action, name]

        if action == "create":
            hypothesis = kwargs.get("hypothesis", f"Pipeline step: {name}")
            cmd.extend(["--hypothesis", hypothesis])
        elif action == "start":
            pass  # sin args extra
        elif action == "log":
            for k, v in kwargs.get("metrics", {}).items():
                cmd.extend(["--metric", f"{k}={v}"])
            if kwargs.get("note"):
                cmd.extend(["--note", str(kwargs["note"])])
        elif action == "finish":
            result = kwargs.get("result", "")
            decision = kwargs.get("decision", "")
            if result:
                cmd.extend(["--result", result])
            if decision:
                cmd.extend(["--decision", decision])

        if self.dry_run:
            print(f"[dry-run] manager: {' '.join(cmd[3:])}")
            return

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(ROOT),
            )
            if proc.returncode != 0:
                print(f"[manager] Warning ({action} {name}): {proc.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"[manager] Timeout en {action} {name}")
        except Exception as e:
            print(f"[manager] Error: {e}")

    # ── Script execution ────────────────────────────────────────

    def _run_script(self, step: dict) -> dict:
        """
        Ejecuta el script de un paso del pipeline.
        Retorna dict con: exit_code, stdout, stderr, metrics, elapsed_s.

        Si el script no existe, retorna exit_code=-1 con mensaje claro.
        Los scripts emiten metricas con el formato:
          METRIC:nombre=valor
        """
        script_path = SCRIPTS_DIR / step["script"]

        if not script_path.exists():
            msg = (
                f"Script no existe: {script_path}\n"
                f"Crear el script para activar este paso del pipeline."
            )
            print(f"\n  [skip] {msg}")
            return {"exit_code": -1, "error": msg, "metrics": {}, "elapsed_s": 0}

        cmd = ["python3", str(script_path)]
        if step.get("args"):
            cmd.extend(step["args"])

        print(f"\n{'─'*60}")
        print(f"Ejecutando: {step['name']}")
        print(f"  Script  : {script_path.name}")
        print(f"  Fase    : {step['phase']}")
        if step.get("args"):
            print(f"  Args    : {' '.join(step['args'])}")
        print(f"{'─'*60}")

        if self.dry_run:
            print(f"  [dry-run] Saltando ejecucion")
            return {"exit_code": 0, "stdout": "[dry-run]", "stderr": "", "metrics": {}, "elapsed_s": 0}

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200,   # 2h max por paso
                cwd=str(ROOT),
            )
            elapsed = time.time() - start_time

            # Parsear metricas del stdout (formato METRIC:key=value)
            metrics: dict = {}
            for line in result.stdout.split("\n"):
                if line.startswith("METRIC:"):
                    try:
                        kv = line[7:].strip()
                        k, _, v = kv.partition("=")
                        metrics[k.strip()] = float(v.strip())
                    except (ValueError, IndexError):
                        pass  # Linea malformada — ignorar

            print(f"\n  Exit code : {result.returncode}")
            print(f"  Duracion  : {elapsed:.1f}s")
            if metrics:
                print(f"  Metricas  : {metrics}")

            if result.returncode != 0:
                err_lines = result.stderr.strip().split("\n")
                tail = "\n    ".join(err_lines[-20:])
                print(f"  Stderr (tail):\n    {tail}")

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "metrics": metrics,
                "elapsed_s": round(elapsed, 1),
            }

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"  TIMEOUT (2h)")
            return {"exit_code": -2, "error": "timeout", "metrics": {}, "elapsed_s": round(elapsed, 1)}
        except Exception as e:
            print(f"  Error inesperado: {e}")
            return {"exit_code": -3, "error": str(e), "metrics": {}, "elapsed_s": 0}

    def _evaluate_gate(self, step: dict, result: dict) -> bool:
        """
        Evalua si el resultado de un paso pasa el quality gate.

        Tipos de gate:
          exit_code  - el exit code debe ser el esperado
          metric     - una metrica del stdout debe cumplir el operador
        """
        gate = step.get("gate")
        if not gate:
            return True

        if gate["type"] == "exit_code":
            passed = result.get("exit_code") == gate["expect"]
            if not passed:
                print(f"  Gate exit_code: esperado {gate['expect']}, obtenido {result.get('exit_code')} -> FAIL")
            return passed

        if gate["type"] == "metric":
            metric_val = result.get("metrics", {}).get(gate["metric"])
            if metric_val is None:
                print(f"  Gate: metrica '{gate['metric']}' no encontrada en stdout -> FAIL")
                print(f"  Metricas disponibles: {list(result.get('metrics', {}).keys())}")
                return False

            op = gate["operator"]
            threshold = gate["threshold"]
            if op == ">=":   passed = metric_val >= threshold
            elif op == ">":  passed = metric_val > threshold
            elif op == "<=": passed = metric_val <= threshold
            elif op == "<":  passed = metric_val < threshold
            elif op == "==": passed = metric_val == threshold
            else:
                print(f"  Gate: operador desconocido '{op}' -> FAIL")
                return False

            status = "PASS" if passed else "FAIL"
            print(f"  Gate: {gate['metric']} = {metric_val} {op} {threshold} -> {status}")
            return passed

        # Tipo desconocido — pasar por defecto con aviso
        print(f"  Gate: tipo '{gate['type']}' desconocido -> ignorando (PASS)")
        return True

    def _attempt_auto_fix(self, step: dict, result: dict) -> bool:
        """
        Intenta aplicar auto-fixes via auto_fixes.py cuando un gate falla.
        Retorna True si el fix se aplico, False si no hay fix disponible.
        """
        if step.get("on_fail") != "auto_fix":
            return False

        if not AUTO_FIXES_SCRIPT.exists():
            print(f"  [auto-fix] Script no encontrado: {AUTO_FIXES_SCRIPT}")
            return False

        print(f"\n  Intentando auto-fix...")

        if self.dry_run:
            print(f"  [dry-run] auto-fix saltado")
            return False

        # Construir un diagnostico minimo desde las metricas del resultado
        diagnosis = {
            "patron_fundamental": "opacidad",   # patron por defecto si no se puede inferir
            "accion": {"tipo": "reformular_dims"},
            "dims_problematicas": [],
        }

        # Guardar diagnostico temporal para que auto_fixes.py lo lea
        diag_file = EXPERIMENTS_DIR / "_auto_fix_diagnosis.json"
        with open(diag_file, "w") as f:
            json.dump(diagnosis, f)

        fix_result = subprocess.run(
            [
                "python3", str(AUTO_FIXES_SCRIPT),
                step["id"],
                "--diagnosis", str(diag_file),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )

        diag_file.unlink(missing_ok=True)

        if fix_result.returncode == 0:
            print(f"  Auto-fix aplicado.")
            return True
        else:
            print(f"  Auto-fix no disponible: {fix_result.stdout[-200:]}")
            return False

    # ── Main loop ───────────────────────────────────────────────

    def run(self, from_step: Optional[str] = None, single_step: Optional[str] = None) -> bool:
        """
        Ejecuta el pipeline completo o parcial.

        Logica de reanudacion:
          - Sin flags    : reanuda desde el primer paso NO completado
          - --from <id>  : fuerza inicio desde ese paso (incluido)
          - --step <id>  : ejecuta solo ese paso

        Retorna True si el pipeline completo con exito, False si se detuvo.
        """
        if not self.state.get("started_at"):
            self.state["started_at"] = datetime.now(timezone.utc).isoformat()
            self._save_state()

        self._notify(f"Pipeline iniciado\nDesde: `{from_step or single_step or 'inicio'}`")

        # Determinar pasos a ejecutar
        if single_step:
            steps = [s for s in PIPELINE_STEPS if s["id"] == single_step]
            if not steps:
                print(f"Error: paso '{single_step}' no encontrado.")
                print(f"Pasos disponibles: {[s['id'] for s in PIPELINE_STEPS]}")
                return False

        elif from_step:
            idx = next((i for i, s in enumerate(PIPELINE_STEPS) if s["id"] == from_step), None)
            if idx is None:
                print(f"Error: paso '{from_step}' no encontrado.")
                print(f"Pasos disponibles: {[s['id'] for s in PIPELINE_STEPS]}")
                return False
            steps = PIPELINE_STEPS[idx:]

        else:
            # Reanudar: saltar pasos ya completados
            completed = set(self.state.get("completed_steps", []))
            steps = [s for s in PIPELINE_STEPS if s["id"] not in completed]

        if not steps:
            print("\nPipeline completado — no hay pasos pendientes.")
            print("Usa --reset para reiniciar el pipeline desde cero.")
            return True

        phases = sorted(set(s["phase"] for s in steps))
        print(f"\n{'='*60}")
        print(f"  PIPELINE SIMBIONTE")
        print(f"  Pasos pendientes : {len(steps)}")
        print(f"  Fases            : {', '.join(phases)}")
        print(f"  Modo             : {'DRY-RUN' if self.dry_run else 'REAL'}")
        print(f"{'='*60}")

        for step in steps:
            step_id = step["id"]
            self.state["current_step"] = step_id
            self._save_state()

            print(f"\n[{step['phase'].upper()}] {step_id}")

            # ── Cost Gate (requiere aprobacion CEO si > $5) ──
            if step.get("cost_gate") and not self.dry_run:
                estimated = step.get("estimated_cost", 0)
                if estimated > 5:
                    approved = self._wait_ceo_approval(step, estimated)
                    if not approved:
                        print(f"  Paso saltado por CEO: {step['name']}")
                        self.state["failed_steps"].append({
                            "id": step_id,
                            "reason": "rejected_by_ceo",
                            "at": datetime.now(timezone.utc).isoformat(),
                        })
                        self._save_state()
                        self._notify(f"Paso saltado por CEO: `{step['name']}`")
                        continue

            # ── Registrar inicio en experiment manager ──
            exp_name = f"pipeline_{step_id}"
            self._manager("create", exp_name, hypothesis=step["name"])
            self._manager("start", exp_name)

            # ── Ejecutar script ──
            result = self._run_script(step)

            # ── Evaluar quality gate ──
            passed = self._evaluate_gate(step, result)

            if not passed:
                # Intentar auto-fix
                fix_applied = self._attempt_auto_fix(step, result)

                if fix_applied:
                    print(f"  Re-ejecutando tras auto-fix...")
                    result = self._run_script(step)
                    passed = self._evaluate_gate(step, result)

                if not passed:
                    # Gate sigue fallando — detener el pipeline
                    gate_info = str(step.get("gate", {}))
                    self._manager(
                        "finish", exp_name,
                        result=f"GATE FALLIDO: {gate_info} | metricas: {result.get('metrics', {})}",
                        decision="Requiere intervencion manual",
                    )

                    self.state["failed_steps"].append({
                        "id": step_id,
                        "reason": "gate_failed",
                        "gate": step.get("gate"),
                        "metrics": result.get("metrics", {}),
                        "at": datetime.now(timezone.utc).isoformat(),
                    })
                    self._save_state()

                    self._notify(
                        f"Gate fallido: `{step['name']}`\n"
                        f"Gate: {step.get('gate')}\n"
                        f"Metricas: {result.get('metrics', {})}",
                        urgent=True,
                    )

                    # Patron 7: contar iteraciones sin mejora
                    if step.get("max_iterations"):
                        self.state["iteration_count"] = self.state.get("iteration_count", 0) + 1
                        count = self.state["iteration_count"]
                        max_iter = step["max_iterations"]
                        print(f"  Iteracion {count}/{max_iter} sin mejora.")

                        if count >= max_iter:
                            self._notify(
                                f"PATRON 7: {max_iter} iteraciones sin mejora.\n"
                                f"Pipeline detenido. Requiere cambio de approach.",
                                urgent=True,
                            )
                            self._save_state()
                            return False

                        self._save_state()
                        continue  # Probar la siguiente iteracion

                    # Sin max_iterations — detencion definitiva
                    print(f"\n  Pipeline detenido en: {step['name']}")
                    print(f"  Para continuar: --from {step_id}")
                    return False

            # ── Gate pasado ──────────────────────────────────────
            metrics = result.get("metrics", {})

            # Actualizar metricas acumuladas
            self.state["metrics"].update(metrics)

            # Registrar en experiment manager
            if metrics:
                self._manager("log", exp_name, metrics=metrics)
            self._manager(
                "finish", exp_name,
                result=f"OK | metricas: {metrics}",
                decision="Continuar al siguiente paso",
            )

            # Marcar como completado
            self.state["completed_steps"].append(step_id)

            # Reset contador de iteraciones en exito
            if step.get("max_iterations"):
                self.state["iteration_count"] = 0

            self._save_state()

            self._notify(
                f"OK: `{step['name']}`\n"
                f"Duracion: {result.get('elapsed_s', '?')}s\n"
                f"Metricas: {metrics}"
            )

        # ── Pipeline completado ──────────────────────────────────
        self._notify(
            f"PIPELINE COMPLETO\n"
            f"Pasos completados: {len(self.state['completed_steps'])}\n"
            f"Metricas finales: {self.state.get('metrics', {})}",
            urgent=True,
        )

        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETADO")
        print(f"  Pasos: {len(self.state['completed_steps'])}")
        print(f"  Metricas finales: {self.state.get('metrics', {})}")
        print(f"{'='*60}")

        return True

    # ── Status ──────────────────────────────────────────────────

    def status(self):
        """Imprime el estado actual del pipeline en formato legible."""
        completed = set(self.state.get("completed_steps", []))
        failed_ids = {f["id"] for f in self.state.get("failed_steps", [])}

        print(f"\n{'='*60}")
        print(f"  PIPELINE STATUS — SIMBIONTE")
        print(f"{'='*60}")
        print(f"  Iniciado        : {self.state.get('started_at', 'No iniciado')}")
        print(f"  Ultima update   : {self.state.get('last_updated', 'N/A')}")
        print(f"  Paso actual     : {self.state.get('current_step', 'Ninguno')}")
        print(f"  Iteraciones     : {self.state.get('iteration_count', 0)}")
        print(f"  Modo            : {'DRY-RUN' if self.dry_run else 'REAL'}")

        print(f"\n  Pasos:")
        for step in PIPELINE_STEPS:
            sid = step["id"]
            if sid in completed:
                mark = "OK "
            elif sid in failed_ids:
                mark = "ERR"
            elif sid == self.state.get("current_step"):
                mark = "RUN"
            else:
                mark = "   "

            cost_str = ""
            if step.get("cost_gate"):
                cost_str = f" [~${step.get('estimated_cost', '?')}]"

            auto_str = "" if step.get("auto", True) else " [CEO approval]"
            print(f"    [{mark}] {sid:25s} | {step['phase']:12s} | {step['name']}{cost_str}{auto_str}")

        if self.state.get("metrics"):
            print(f"\n  Metricas acumuladas:")
            for k, v in self.state["metrics"].items():
                print(f"    {k} = {v}")

        if self.state.get("failed_steps"):
            print(f"\n  Pasos fallidos:")
            for f in self.state["failed_steps"]:
                print(f"    - {f['id']} ({f.get('reason', '?')}) @ {f.get('at', '?')[:19]}")

        print(f"{'='*60}")
        print(f"\n  Comandos utiles:")
        print(f"    Continuar      : python3 {__file__} --from <step_id>")
        print(f"    Paso unico     : python3 {__file__} --step <step_id>")
        print(f"    Dry-run        : python3 {__file__} --dry-run")
        print(f"    Resetear       : python3 {__file__} --reset")
        print()


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="OMNI-MIND Pipeline Runner — Orquestador de entrenamiento Simbionte",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 pipeline_runner.py --status           # Ver estado
  python3 pipeline_runner.py --dry-run          # Simular sin ejecutar
  python3 pipeline_runner.py                    # Ejecutar (reanuda desde ultimo paso)
  python3 pipeline_runner.py --from train_baseline
  python3 pipeline_runner.py --step data_audit
  python3 pipeline_runner.py --reset            # Resetear y empezar de cero
        """,
    )
    parser.add_argument(
        "--from", dest="from_step", metavar="STEP_ID",
        help="Empezar desde este paso (inclusive)",
    )
    parser.add_argument(
        "--step", metavar="STEP_ID",
        help="Ejecutar solo este paso",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Mostrar estado del pipeline y salir",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simular el pipeline sin ejecutar ningun script",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Borrar estado del pipeline y empezar de cero",
    )
    parser.add_argument(
        "--list-steps", action="store_true",
        help="Listar todos los pasos del pipeline y salir",
    )

    args = parser.parse_args()

    if args.reset:
        if PIPELINE_STATE_FILE.exists():
            PIPELINE_STATE_FILE.unlink()
            print(f"Pipeline state borrado: {PIPELINE_STATE_FILE}")
        else:
            print("No habia estado guardado.")
        return

    if args.list_steps:
        print(f"\nPasos del pipeline ({len(PIPELINE_STEPS)}):")
        for s in PIPELINE_STEPS:
            cost_str = f" [~${s.get('estimated_cost', 0)}]" if s.get("cost_gate") else ""
            auto_str = "" if s.get("auto", True) else " [requiere CEO]"
            print(f"  {s['id']:25s} | {s['phase']:12s}{cost_str}{auto_str}")
        return

    runner = PipelineRunner(dry_run=args.dry_run)

    if args.status:
        runner.status()
        return

    success = runner.run(from_step=args.from_step, single_step=args.step)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
