"""AgenteReal — Base para todos los agentes de OMNI-MIND.

Un agente real tiene un loop continuo:
  OBSERVAR → RAZONAR → PLANIFICAR → ACTUAR → REFLEXIONAR → RECORDAR

Cada agente hereda de AgenteReal e implementa:
  - observar() → dict          # Qué está pasando en el mundo
  - decidir(observacion) → str # Qué hacer (usa LLM para razonar)
  - actuar(decision) → dict    # Ejecutar la decisión
  - herramientas() → list      # Qué puede hacer este agente

El loop, la memoria, la reflexión y la comunicación son automáticos.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

from .memoria import Memoria
from .comunicacion import dejar_marca, leer_marcas, marcar_como_leida, marcas_pendientes

# ACD pipeline — imports opcionales para evitar dependencias circulares
try:
    from .perceptor import percibir
    from .razonador import razonar as _razonar_acd, diagnostico_a_dict
    from .generador import generar_prompt_acd, verificar_output
    _ACD_DISPONIBLE = True
except ImportError:
    _ACD_DISPONIBLE = False

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))
MOTOR_DIR = Path(__file__).parent.parent.parent


class AgenteReal(ABC):
    """Base para un agente real con loop de razonamiento."""

    def __init__(self, nombre: str, rol: str, objetivo: str,
                 personalidad: str = "", model: str = "claude-sonnet-4-20250514"):
        self.nombre = nombre
        self.rol = rol
        self.objetivo = objetivo
        self.personalidad = personalidad
        self.model = model
        self.memoria = Memoria(nombre)
        self.ciclo = 0
        self.activo = True
        self.max_ciclos = 0  # 0 = infinito
        self.pausa_entre_ciclos = 30  # segundos
        self._log_prefix = f"[{nombre.upper()}]"

    # ═══════════════════════════════════════════════════════
    # MÉTODOS QUE CADA AGENTE DEBE IMPLEMENTAR
    # ═══════════════════════════════════════════════════════

    @abstractmethod
    async def observar(self) -> dict:
        """Observa el estado del mundo. Devuelve datos crudos."""
        ...

    @abstractmethod
    async def actuar(self, plan: dict) -> dict:
        """Ejecuta una acción concreta. Devuelve resultado."""
        ...

    def herramientas(self) -> list[dict]:
        """Lista de herramientas/acciones disponibles para este agente.
        Override en subclase para añadir herramientas específicas."""
        return [
            {"nombre": "dejar_marca", "desc": "Comunicar algo a otro agente via tablón"},
            {"nombre": "esperar", "desc": "No hacer nada este ciclo"},
            {"nombre": "escalar", "desc": "Pedir ayuda a Jesús o al Traductor"},
        ]

    # ═══════════════════════════════════════════════════════
    # LLM — El cerebro del agente
    # ═══════════════════════════════════════════════════════

    async def pensar(self, system: str, user: str, max_tokens: int = 2048) -> str:
        """Una llamada al LLM. El agente 'piensa'."""
        if not ANTHROPIC_KEY:
            return '{"accion": "esperar", "razon": "Sin API key"}'

        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            data = r.json()
            return data.get("content", [{}])[0].get("text", "")

    def _parsear_json(self, texto: str) -> dict:
        """Extrae JSON de una respuesta del LLM."""
        clean = texto
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in clean:
            parts = clean.split("```")
            if len(parts) >= 3:
                clean = parts[1]
        try:
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(clean[start:end])
        except json.JSONDecodeError:
            pass
        return {"raw": texto[:500]}

    # ═══════════════════════════════════════════════════════
    # ACD — Pipeline Analizar-Comprender-Diagnosticar
    # ═══════════════════════════════════════════════════════

    async def pensar_acd(self, system: str, user: str, max_tokens: int = 2048) -> str:
        """Piensa con el pipeline ACD: analiza input -> genera guiado -> verifica output.

        El LLM recibe las reglas ACD en el system prompt y su output
        es verificado contra las 48 reglas del Razonador.
        """
        if not _ACD_DISPONIBLE:
            return await self.pensar(system, user, max_tokens)

        # 1. Analizar el user message con Perceptor+Razonador
        try:
            estructura = await percibir(user[:2000])
            if "error" not in estructura:
                diag = diagnostico_a_dict(_razonar_acd(estructura))
            else:
                diag = None
        except Exception:
            diag = None

        # 2. Enriquecer system prompt con reglas ACD + hallazgos del input
        system_acd = system + "\n\n" + generar_prompt_acd(diagnostico_input=diag)

        # 3. Generar con el LLM
        response = await self.pensar(system_acd, user, max_tokens)

        return response

    async def analizar_con_acd(self, texto: str) -> dict:
        """Analiza un texto con el pipeline ACD completo. Devuelve diagnostico."""
        if not _ACD_DISPONIBLE:
            return {}
        try:
            estructura = await percibir(texto[:2000])
            if "error" not in estructura:
                return diagnostico_a_dict(_razonar_acd(estructura))
        except Exception:
            pass
        return {}

    # ═══════════════════════════════════════════════════════
    # RAZONAR — Decidir qué hacer (el corazón del agente)
    # ═══════════════════════════════════════════════════════

    async def razonar(self, observacion: dict) -> dict:
        """Usa el LLM para razonar sobre la observación y decidir qué hacer.

        Devuelve: {"accion": str, "parametros": dict, "razon": str, "confianza": float}
        """
        # Construir contexto rico
        memoria_ctx = self.memoria.resumen_para_prompt(json.dumps(observacion)[:500])
        herramientas_desc = "\n".join(
            f"  - {h['nombre']}: {h['desc']}" for h in self.herramientas()
        )

        # Marcas de otros agentes
        marcas = leer_marcas(self.nombre, solo_nuevas=True)
        marcas_ctx = ""
        if marcas:
            marcas_ctx = "\nMENSAJES DE OTROS AGENTES:\n"
            for m in marcas[:5]:
                marcas_ctx += f"  [{m['emisor']}→{m['tipo']}] {json.dumps(m['contenido'], ensure_ascii=False)[:200]}\n"
                marcar_como_leida(self.nombre, m["id"])

        system = f"""Eres {self.nombre}, un agente autónomo de OMNI-MIND.

ROL: {self.rol}
OBJETIVO: {self.objetivo}
{f'PERSONALIDAD: {self.personalidad}' if self.personalidad else ''}
CICLO ACTUAL: {self.ciclo}

{memoria_ctx}

HERRAMIENTAS DISPONIBLES:
{herramientas_desc}

REGLAS:
1. Piensa paso a paso antes de decidir
2. Si no estás seguro, elige "esperar" o "escalar"
3. Prioriza acciones que acerquen al OBJETIVO
4. Aprende de tus errores pasados (mira tu MEMORIA)
5. Si otro agente te dejó un mensaje, responde o actúa

RESPONDE EN JSON:
{{
  "pensamiento": "Tu razonamiento paso a paso (qué observas, qué significa, qué opciones tienes)",
  "accion": "nombre_de_herramienta",
  "parametros": {{}},
  "razon": "Por qué eliges esta acción (1 frase)",
  "confianza": 0.0-1.0,
  "mensaje_para_agente": {{"destino": "nombre", "contenido": "..."}} // opcional
}}"""

        user = f"""OBSERVACIÓN DEL MUNDO:
{json.dumps(observacion, ensure_ascii=False, indent=2)[:3000]}
{marcas_ctx}

¿Qué haces? Razona paso a paso y decide."""

        self._log("🧠 Razonando...")
        response = await self.pensar_acd(system, user)
        plan = self._parsear_json(response)

        # Si quiere comunicarse con otro agente
        msg = plan.get("mensaje_para_agente")
        if msg and isinstance(msg, dict) and msg.get("destino"):
            dejar_marca(
                self.nombre,
                "solicitud",
                {"mensaje": msg.get("contenido", ""), "contexto": plan.get("razon", "")},
                prioridad=3,
                destino=msg["destino"],
            )
            self._log(f"📨 Mensaje → {msg['destino']}")

        return plan

    # ═══════════════════════════════════════════════════════
    # REFLEXIONAR — Aprender del resultado
    # ═══════════════════════════════════════════════════════

    async def reflexionar(self, observacion: dict, plan: dict, resultado: dict) -> str:
        """Reflexiona sobre lo que pasó y extrae aprendizajes."""

        system = f"""Eres {self.nombre}. Acabas de ejecutar una acción.
Reflexiona: ¿funcionó? ¿qué aprendiste? ¿qué harías diferente?

RESPONDE EN JSON:
{{
  "funcionó": true/false,
  "reflexion": "1-2 frases sobre qué pasó",
  "aprendizaje": "1 frase de lo que aprendiste (o null si nada nuevo)",
  "siguiente_prioridad": "qué debería hacer en el próximo ciclo"
}}"""

        user = f"""PLAN: {json.dumps(plan, ensure_ascii=False)[:500]}
RESULTADO: {json.dumps(resultado, ensure_ascii=False)[:500]}

Reflexiona."""

        response = await self.pensar_acd(system, user, max_tokens=512)
        reflexion = self._parsear_json(response)

        # Guardar aprendizaje si hay
        aprendizaje = reflexion.get("aprendizaje")
        if aprendizaje and aprendizaje != "null" and len(aprendizaje) > 5:
            self.memoria.aprender(
                "experiencia",
                aprendizaje,
                confianza=0.5 if reflexion.get("funcionó") else 0.3,
            )
            self._log(f"📚 Aprendizaje: {aprendizaje[:60]}")

        return reflexion.get("reflexion", "Sin reflexión")

    # ═══════════════════════════════════════════════════════
    # LOOP PRINCIPAL — El corazón del agente
    # ═══════════════════════════════════════════════════════

    async def loop(self, max_ciclos: int = 0, pausa: int = 0):
        """Loop principal del agente. Corre hasta que se detenga."""
        if max_ciclos > 0:
            self.max_ciclos = max_ciclos
        if pausa > 0:
            self.pausa_entre_ciclos = pausa

        self._log(f"🚀 Iniciando — objetivo: {self.objetivo[:60]}")
        self._log(f"   Ciclos: {'infinito' if self.max_ciclos == 0 else self.max_ciclos}")

        while self.activo:
            self.ciclo += 1
            if self.max_ciclos > 0 and self.ciclo > self.max_ciclos:
                self._log(f"🏁 {self.max_ciclos} ciclos completados")
                break

            self._log(f"\n{'━' * 50}")
            self._log(f"CICLO {self.ciclo}")
            self._log(f"{'━' * 50}")

            try:
                await self._ejecutar_ciclo()
            except Exception as e:
                self._log(f"❌ Error en ciclo: {e}")
                self.memoria.aprender("error", f"Error en ciclo {self.ciclo}: {str(e)[:100]}", 0.8)
                # Dejar marca de error para otros agentes
                dejar_marca(self.nombre, "alerta", {
                    "tipo": "error",
                    "ciclo": self.ciclo,
                    "error": str(e)[:200],
                })

            # Persistir memoria después de cada ciclo
            self.memoria.persistir()

            # Pausa entre ciclos
            if self.activo and (self.max_ciclos == 0 or self.ciclo < self.max_ciclos):
                self._log(f"⏳ Pausa {self.pausa_entre_ciclos}s...")
                await asyncio.sleep(self.pausa_entre_ciclos)

        self._log(f"🛑 Detenido tras {self.ciclo} ciclos")

    async def _ejecutar_ciclo(self):
        """Un ciclo completo: observar → razonar → actuar → reflexionar."""
        t0 = time.time()

        # 1. OBSERVAR
        self._log("👁️  Observando...")
        observacion = await self.observar()
        self.memoria.set_trabajo("observacion", observacion)

        # 2. RAZONAR
        plan = await self.razonar(observacion)
        accion = plan.get("accion", "esperar")
        confianza = plan.get("confianza", 0.5)
        self._log(f"🎯 Decisión: {accion} (confianza: {confianza:.1f})")
        self._log(f"   Razón: {plan.get('razon', '?')[:80]}")

        # 3. ACTUAR
        if accion == "esperar":
            self._log("💤 Esperando (nada que hacer)")
            resultado = {"status": "idle", "razon": plan.get("razon", "")}
        elif accion == "escalar":
            self._log("🆘 Escalando a Jesús/Traductor")
            dejar_marca(self.nombre, "pregunta", {
                "pregunta": plan.get("razon", "Necesito ayuda"),
                "contexto": json.dumps(observacion, ensure_ascii=False)[:500],
            }, prioridad=1, destino="traductor")
            resultado = {"status": "escalado"}
        elif accion == "dejar_marca":
            params = plan.get("parametros", {})
            dejar_marca(
                self.nombre,
                params.get("tipo", "solicitud"),
                params.get("contenido", {}),
                prioridad=params.get("prioridad", 5),
                destino=params.get("destino"),
            )
            resultado = {"status": "marca_dejada"}
        else:
            self._log(f"⚡ Ejecutando: {accion}")
            resultado = await self.actuar(plan)

        # 4. REFLEXIONAR
        self._log("🪞 Reflexionando...")
        reflexion = await self.reflexionar(observacion, plan, resultado)
        self._log(f"   {reflexion[:80]}")

        # 5. RECORDAR
        self.memoria.registrar_episodio(
            ciclo=self.ciclo,
            observacion=observacion,
            decision=f"{accion}: {plan.get('razon', '')[:100]}",
            accion=accion,
            resultado=resultado,
            reflexion=reflexion,
        )

        duracion = round(time.time() - t0, 1)
        self._log(f"⏱️  Ciclo completado en {duracion}s")

    # ═══════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  {ts} {self._log_prefix} {msg}")

    async def ejecutar_comando(self, comando: str, timeout: int = 120) -> dict:
        """Ejecuta un comando shell y devuelve resultado."""
        try:
            result = subprocess.run(
                comando, shell=True,
                capture_output=True, text=True,
                cwd=str(MOTOR_DIR),
                timeout=timeout,
                env={**os.environ},
            )
            return {
                "exito": result.returncode == 0,
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {"exito": False, "error": f"Timeout {timeout}s"}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def leer_archivo(self, ruta_relativa: str) -> str:
        """Lee un archivo del repo."""
        path = MOTOR_DIR / ruta_relativa
        try:
            return path.read_text()[:8000]
        except Exception:
            return f"[No se pudo leer {ruta_relativa}]"

    def detener(self):
        """Detiene el loop del agente."""
        self.activo = False
