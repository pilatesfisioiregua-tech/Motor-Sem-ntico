"""Sistema de Memoria Persistente para Agentes Reales.

Cada agente tiene:
- Memoria episódica: qué hizo, qué pasó, qué aprendió (por ciclo)
- Memoria semántica: conocimiento acumulado (hechos, patrones, creencias)
- Memoria de trabajo: contexto del ciclo actual

Almacenamiento: JSON files en memoria/<agente>/
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

MEMORIA_DIR = Path(__file__).parent.parent.parent / "memoria"


class Memoria:
    """Memoria persistente de un agente."""

    def __init__(self, agente: str):
        self.agente = agente
        self.dir = MEMORIA_DIR / agente
        self.dir.mkdir(parents=True, exist_ok=True)

        # Cargar memorias existentes
        self.episodica: list[dict] = self._cargar("episodica", [])
        self.semantica: dict = self._cargar("semantica", {
            "hechos": [],
            "patrones": [],
            "creencias": {},
            "aprendizajes": [],
        })
        self.trabajo: dict = {}  # Se resetea cada ciclo

    # ─── Persistencia ───

    def _cargar(self, nombre: str, default: Any) -> Any:
        path = self.dir / f"{nombre}.json"
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return default

    def _guardar(self, nombre: str, data: Any):
        path = self.dir / f"{nombre}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))

    def persistir(self):
        """Guarda todo a disco."""
        # Limitar episódica a últimos 100 episodios
        self._guardar("episodica", self.episodica[-100:])
        self._guardar("semantica", self.semantica)

    # ─── Memoria Episódica ───

    def registrar_episodio(self, ciclo: int, observacion: dict, decision: str,
                           accion: str, resultado: dict, reflexion: str):
        """Registra un episodio completo (1 ciclo del loop)."""
        self.episodica.append({
            "ciclo": ciclo,
            "timestamp": datetime.now().isoformat(),
            "observacion": observacion,
            "decision": decision,
            "accion": accion,
            "resultado": resultado,
            "reflexion": reflexion,
        })

    def ultimos_episodios(self, n: int = 5) -> list[dict]:
        """Últimos N episodios para contexto."""
        return self.episodica[-n:]

    def episodios_relevantes(self, contexto: str, n: int = 3) -> list[dict]:
        """Busca episodios relevantes al contexto actual (keyword match simple)."""
        palabras = set(contexto.lower().split())
        scored = []
        for ep in self.episodica:
            ep_text = json.dumps(ep, ensure_ascii=False).lower()
            overlap = sum(1 for p in palabras if p in ep_text)
            if overlap > 0:
                scored.append((overlap, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:n]]

    # ─── Memoria Semántica ───

    def aprender(self, tipo: str, contenido: str, confianza: float = 0.5):
        """Registra un aprendizaje nuevo."""
        entry = {
            "tipo": tipo,  # hecho, patron, regla, error
            "contenido": contenido,
            "confianza": confianza,
            "timestamp": datetime.now().isoformat(),
            "veces_confirmado": 1,
        }

        # Si ya existe un aprendizaje similar, reforzar
        for a in self.semantica["aprendizajes"]:
            if a["contenido"] == contenido:
                a["confianza"] = min(a["confianza"] + 0.1, 0.99)
                a["veces_confirmado"] += 1
                return

        self.semantica["aprendizajes"].append(entry)
        # Limitar a 50 aprendizajes
        if len(self.semantica["aprendizajes"]) > 50:
            # Quitar los de menor confianza
            self.semantica["aprendizajes"].sort(key=lambda x: x["confianza"], reverse=True)
            self.semantica["aprendizajes"] = self.semantica["aprendizajes"][:50]

    def creer(self, clave: str, valor: Any):
        """Actualiza una creencia del agente."""
        self.semantica["creencias"][clave] = {
            "valor": valor,
            "actualizado": datetime.now().isoformat(),
        }

    def creencia(self, clave: str, default: Any = None) -> Any:
        """Lee una creencia."""
        c = self.semantica["creencias"].get(clave)
        return c["valor"] if c else default

    def aprendizajes_relevantes(self, contexto: str, n: int = 5) -> list[dict]:
        """Aprendizajes relevantes al contexto."""
        palabras = set(contexto.lower().split())
        scored = []
        for a in self.semantica["aprendizajes"]:
            text = a["contenido"].lower()
            overlap = sum(1 for p in palabras if p in text)
            score = overlap * a["confianza"]
            if score > 0:
                scored.append((score, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:n]]

    # ─── Memoria de Trabajo ───

    def set_trabajo(self, clave: str, valor: Any):
        self.trabajo[clave] = valor

    def get_trabajo(self, clave: str, default: Any = None) -> Any:
        return self.trabajo.get(clave, default)

    def reset_trabajo(self):
        self.trabajo = {}

    # ─── Resumen para prompt ───

    def resumen_para_prompt(self, contexto: str = "") -> str:
        """Genera un resumen de memoria para inyectar en el prompt del LLM."""
        partes = []

        # Últimos episodios
        ultimos = self.ultimos_episodios(3)
        if ultimos:
            partes.append("MEMORIA RECIENTE:")
            for ep in ultimos:
                partes.append(f"  Ciclo {ep['ciclo']}: {ep['decision'][:80]} → {ep['reflexion'][:80]}")

        # Aprendizajes relevantes
        if contexto:
            relevantes = self.aprendizajes_relevantes(contexto)
            if relevantes:
                partes.append("\nAPRENDIZAJES RELEVANTES:")
                for a in relevantes:
                    partes.append(f"  [{a['confianza']:.1f}] {a['contenido'][:100]}")

        # Creencias actuales
        if self.semantica["creencias"]:
            partes.append("\nCREENCIAS ACTUALES:")
            for k, v in list(self.semantica["creencias"].items())[:5]:
                partes.append(f"  {k}: {v['valor']}")

        return "\n".join(partes) if partes else "[Sin memoria previa]"
