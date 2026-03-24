"""IPC avanzado — Control Plane, Federated Learning, Contract Net, Discovery, App Store.

5 conceptos top mundial implementados:

1. Control Plane vs Data Plane (Unix signals):
   Separar lifecycle (pausar, reconfigurar) de trabajo (datos, recetas).

2. Federated Learning (Google):
   Compartir GRADIENTES (recetas anonimizadas), no datos de negocio.

3. Contract Net Protocol (FIPA):
   Subasta de tareas entre agentes por competencia estimada.

4. Discovery Service (D-Bus):
   Registro de capacidades, descubrimiento automatico.

5. App Store curado (npm + Apple):
   Catalogo con versionado, quality gates, reputation score.
"""
from __future__ import annotations

import time
import structlog
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

log = structlog.get_logger()


# ============================================================
# 1. CONTROL PLANE vs DATA PLANE (Unix signals)
# ============================================================

class TipoMensaje(str, Enum):
    """Separacion explicita de plano control vs plano datos."""
    # Control plane (lifecycle)
    SIGNAL_PAUSE = "signal:pause"
    SIGNAL_RESUME = "signal:resume"
    SIGNAL_RELOAD = "signal:reload"
    SIGNAL_SHUTDOWN = "signal:shutdown"
    SIGNAL_HEALTH = "signal:health"
    # Data plane (trabajo)
    DATA_TRANSFERENCIA = "data:transferencia"
    DATA_RECETA = "data:receta"
    DATA_TELEMETRIA = "data:telemetria"
    DATA_ALERTA = "data:alerta"
    DATA_HEARTBEAT = "data:heartbeat"


@dataclass
class MensajeIPC:
    """Mensaje entre apps via el bus IPC del OS."""
    origen_pid: str
    destino_pid: str              # "*" = broadcast
    tipo: TipoMensaje
    payload: dict = field(default_factory=dict)
    prioridad: int = 5           # 1=urgente, 10=background
    requiere_cr1: bool = False
    timestamp: float = field(default_factory=time.time)
    respondido: bool = False
    # Metadata IPC
    gap: str = ""
    similaridad: float = 0.0
    confianza: float = 0.0


class BusIPC:
    """Bus de comunicacion con planos separados.

    Control plane: procesado INMEDIATAMENTE (no encolado).
    Data plane: encolado y procesado por orden de prioridad.
    """

    def __init__(self):
        self._cola_datos: list[MensajeIPC] = []
        self._historial: list[MensajeIPC] = []
        self._handlers_control: dict[TipoMensaje, list[Callable]] = {}

    def registrar_handler_control(self, tipo: TipoMensaje,
                                   handler: Callable) -> None:
        """Registra handler para mensajes del control plane."""
        self._handlers_control.setdefault(tipo, []).append(handler)

    def enviar(self, mensaje: MensajeIPC) -> None:
        """Envia un mensaje. Control plane se procesa inmediatamente."""
        if mensaje.tipo.value.startswith("signal:"):
            # Control plane: ejecucion inmediata
            handlers = self._handlers_control.get(mensaje.tipo, [])
            for h in handlers:
                try:
                    h(mensaje)
                except Exception as e:
                    log.warning("ipc.handler_error", tipo=mensaje.tipo, error=str(e)[:80])
            self._historial.append(mensaje)
        else:
            # Data plane: encolar por prioridad
            self._cola_datos.append(mensaje)
            self._cola_datos.sort(key=lambda m: m.prioridad)

    def recibir(self, pid: str, limite: int = 10) -> list[MensajeIPC]:
        """Lee mensajes pendientes (data plane) para un proceso."""
        propios = [m for m in self._cola_datos
                   if m.destino_pid == pid or m.destino_pid == "*"]
        self._cola_datos = [m for m in self._cola_datos
                            if m.destino_pid != pid and m.destino_pid != "*"]
        self._historial.extend(propios[:limite])
        return propios[:limite]

    def broadcast_control(self, origen: str, tipo: TipoMensaje,
                          payload: dict = None):
        """Broadcast de signal a todos los procesos."""
        self.enviar(MensajeIPC(
            origen_pid=origen, destino_pid="*",
            tipo=tipo, payload=payload or {}, prioridad=1))

    @property
    def stats(self) -> dict:
        return {
            "pendientes_datos": len(self._cola_datos),
            "historial": len(self._historial),
            "handlers_control": {
                t.value: len(hs) for t, hs in self._handlers_control.items()},
        }


# ============================================================
# 2. FEDERATED LEARNING — gradientes, no datos
# ============================================================

@dataclass
class GradienteReceta:
    """Un 'gradiente' anonimizado: lo que funciono sin datos del negocio.

    NO contiene: nombres clientes, pagos, conversaciones, datos personales.
    SI contiene: que tipo de gap se cerro, con que tipo de receta, con que tasa.
    """
    gap: str                     # F3_baja, F6_baja
    sector: str                  # wellness, dental, saas
    tamano: str                  # micro, pyme, mediana
    receta_tipo: str             # "NPS_trimestral", "referidos_15pct"
    tasa_cierre: float           # 0.82
    n_ejecuciones: int           # 50
    ciclos_para_cerrar: int      # 3
    contexto_gap: str            # "F3 score 3/10, 22 clientes, sin medicion satisfaccion"
    # Anonimizado: sin tenant_id, sin nombres, sin datos de negocio


class FederatedLearning:
    """Compartir aprendizajes sin compartir datos.

    Cada app publica GRADIENTES (recetas anonimizadas con resultados).
    El ecosistema agrega gradientes de N apps para mejorar a todas.
    """

    def __init__(self):
        self._gradientes: list[GradienteReceta] = []

    def publicar_gradiente(self, gradiente: GradienteReceta):
        """Una app publica su aprendizaje anonimizado."""
        self._gradientes.append(gradiente)
        log.debug("federated.gradiente_publicado",
                  gap=gradiente.gap, tasa=gradiente.tasa_cierre)

    def agregar_gradientes(self, gap: str,
                            min_tasa: float = 0.5,
                            min_ejecuciones: int = 5) -> list[GradienteReceta]:
        """Agrega gradientes relevantes para un gap especifico."""
        return [
            g for g in self._gradientes
            if g.gap == gap
            and g.tasa_cierre >= min_tasa
            and g.n_ejecuciones >= min_ejecuciones
        ]

    def mejor_receta_para(self, gap: str, sector: str = None,
                           tamano: str = None) -> Optional[GradienteReceta]:
        """Encuentra la mejor receta para un gap, priorizando contexto similar."""
        candidatos = self.agregar_gradientes(gap)
        if not candidatos:
            return None

        # Priorizar por: mismo sector > mismo tamano > mayor tasa
        def score(g: GradienteReceta) -> float:
            s = g.tasa_cierre
            if sector and g.sector == sector:
                s += 0.2
            if tamano and g.tamano == tamano:
                s += 0.1
            return s

        candidatos.sort(key=score, reverse=True)
        return candidatos[0]

    @property
    def total_gradientes(self) -> int:
        return len(self._gradientes)


# ============================================================
# 3. CONTRACT NET PROTOCOL (FIPA) — subasta de tareas
# ============================================================

@dataclass
class Subasta:
    """Una subasta de tarea entre agentes."""
    id: str
    tarea: str              # Descripcion de la tarea
    gap: str                # Gap a cerrar
    requisitos: dict = field(default_factory=dict)
    pujas: list[dict] = field(default_factory=list)
    ganador: Optional[str] = None
    cerrada: bool = False

    def pujar(self, agente_id: str, competencia: float,
              coste_estimado: float, tiempo_estimado_min: int):
        """Un agente puja por la tarea."""
        if self.cerrada:
            return
        self.pujas.append({
            "agente": agente_id,
            "competencia": competencia,    # 0-1
            "coste": coste_estimado,
            "tiempo": tiempo_estimado_min,
            "score": competencia * 0.6 + (1 - min(coste_estimado, 1)) * 0.3 + (1 - min(tiempo_estimado_min / 60, 1)) * 0.1,
        })

    def adjudicar(self) -> Optional[str]:
        """Adjudica al mejor postor (mayor score)."""
        if not self.pujas or self.cerrada:
            return None
        self.pujas.sort(key=lambda p: p["score"], reverse=True)
        self.ganador = self.pujas[0]["agente"]
        self.cerrada = True
        return self.ganador


class ContractNet:
    """Protocolo Contract Net para asignacion de tareas."""

    def __init__(self):
        self._subastas: dict[str, Subasta] = {}
        self._counter = 0

    def crear_subasta(self, tarea: str, gap: str,
                      requisitos: dict = None) -> Subasta:
        self._counter += 1
        sid = f"sub_{self._counter}"
        subasta = Subasta(id=sid, tarea=tarea, gap=gap,
                          requisitos=requisitos or {})
        self._subastas[sid] = subasta
        return subasta

    def obtener(self, sid: str) -> Optional[Subasta]:
        return self._subastas.get(sid)


# ============================================================
# 4. DISCOVERY SERVICE (D-Bus) — registro de capacidades
# ============================================================

@dataclass
class ServicioRegistrado:
    """Un servicio/capacidad publicado por un agente."""
    agente_id: str
    nombre: str              # "diagnostico_acd", "prescripcion_F3"
    capacidades: list[str]   # ["F3", "F1", "depuracion"]
    version: str = "1.0.0"
    estado: str = "activo"   # activo | pausado | degradado
    metadata: dict = field(default_factory=dict)


class Discovery:
    """Servicio de descubrimiento de capacidades (D-Bus pattern).

    Los agentes publican que saben hacer.
    El OS ruta tareas al agente mas capaz.
    """

    def __init__(self):
        self._servicios: dict[str, ServicioRegistrado] = {}

    def registrar(self, servicio: ServicioRegistrado):
        """Un agente publica sus capacidades."""
        key = f"{servicio.agente_id}:{servicio.nombre}"
        self._servicios[key] = servicio

    def buscar(self, capacidad: str) -> list[ServicioRegistrado]:
        """Busca agentes con una capacidad especifica."""
        return [
            s for s in self._servicios.values()
            if capacidad in s.capacidades and s.estado == "activo"
        ]

    def buscar_por_gap(self, gap: str) -> list[ServicioRegistrado]:
        """Busca agentes que pueden cerrar un gap."""
        funcion = gap.split("_")[0]  # "F3_baja" → "F3"
        return self.buscar(funcion)

    def listar(self) -> list[dict]:
        return [
            {"agente": s.agente_id, "nombre": s.nombre,
             "capacidades": s.capacidades, "estado": s.estado}
            for s in self._servicios.values()
        ]


# ============================================================
# 5. APP STORE CURADO (npm + Apple)
# ============================================================

@dataclass
class RecetaPublicada:
    """Una receta en el App Store del ecosistema."""
    id: str
    nombre: str
    gap: str                     # F3_baja, F6_baja
    sector: str                  # wellness, dental, saas, "*"
    version: str = "1.0.0"
    receta: dict = field(default_factory=dict)
    # Quality gates
    tasa_cierre: float = 0.0
    n_ejecuciones: int = 0
    n_tenants_exitosos: int = 0
    # Reputation
    rating: float = 0.0          # 0-5
    descargas: int = 0
    reportes: int = 0            # Reportes negativos
    curada: bool = False         # Revisada por el OS

    @property
    def confianza(self) -> float:
        """Score de confianza compuesto."""
        if self.n_ejecuciones < 5:
            return 0.0
        base = self.tasa_cierre
        multi_tenant = min(self.n_tenants_exitosos / 3, 1.0) * 0.2
        volumen = min(self.n_ejecuciones / 50, 1.0) * 0.1
        penalizacion = min(self.reportes * 0.05, 0.3)
        return max(0, base + multi_tenant + volumen - penalizacion)


class AppStoreCurado:
    """Catalogo curado de recetas del ecosistema.

    Quality gates:
      - Min 5 ejecuciones
      - Min 0.5 tasa cierre
      - Versionado semver
      - Reputation score

    El MOAT: N apps × M ciclos × K gaps = catalogo intransferible.
    """

    def __init__(self):
        self._catalogo: dict[str, RecetaPublicada] = {}
        self._counter = 0

    def publicar(self, nombre: str, gap: str, sector: str,
                 receta: dict, tasa_cierre: float,
                 n_ejecuciones: int) -> Optional[str]:
        """Publica una receta (con quality gate)."""
        # Quality gate: minimos
        if n_ejecuciones < 5:
            log.debug("appstore.rechazada_pocas_ejecuciones", nombre=nombre)
            return None
        if tasa_cierre < 0.5:
            log.debug("appstore.rechazada_baja_tasa", nombre=nombre)
            return None

        self._counter += 1
        rid = f"receta_{self._counter}"

        self._catalogo[rid] = RecetaPublicada(
            id=rid, nombre=nombre, gap=gap, sector=sector,
            receta=receta, tasa_cierre=tasa_cierre,
            n_ejecuciones=n_ejecuciones,
        )
        log.info("appstore.publicada", id=rid, nombre=nombre, gap=gap)
        return rid

    def buscar(self, gap: str, sector: str = None,
               min_confianza: float = 0.5,
               limite: int = 10) -> list[RecetaPublicada]:
        """Busca recetas por gap, sector y confianza."""
        resultados = []
        for r in self._catalogo.values():
            if r.gap != gap:
                continue
            if sector and r.sector != sector and r.sector != "*":
                continue
            if r.confianza < min_confianza:
                continue
            resultados.append(r)

        resultados.sort(key=lambda r: r.confianza, reverse=True)
        return resultados[:limite]

    def descargar(self, receta_id: str) -> Optional[dict]:
        """Descarga una receta (incrementa contador)."""
        r = self._catalogo.get(receta_id)
        if r:
            r.descargas += 1
            return r.receta
        return None

    def reportar(self, receta_id: str):
        """Reporta una receta como problematica."""
        r = self._catalogo.get(receta_id)
        if r:
            r.reportes += 1

    @property
    def stats(self) -> dict:
        return {
            "total_recetas": len(self._catalogo),
            "curadas": sum(1 for r in self._catalogo.values() if r.curada),
            "descargas_total": sum(r.descargas for r in self._catalogo.values()),
        }
