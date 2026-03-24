"""Sandboxing + Entitlements + Intents + Hooks + Activation Events + Durable Objects.

5 conceptos top mundial para apps (exocortex):

1. Sandboxing + Entitlements (iOS): Aislamiento + permisos granulares
2. Intents (Android): Mensajes tipados para interop sin acoplamiento
3. Durable Objects (Cloudflare): Agente con identidad + memoria persistente
4. Hooks — Actions + Filters (WordPress): Extensibilidad sin tocar nucleo
5. Activation Events (VSCode): Carga bajo demanda por trigger
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Any, Callable, Optional

log = structlog.get_logger()


# ============================================================
# 1. SANDBOXING + ENTITLEMENTS (iOS)
# ============================================================

class Entitlement(Flag):
    """Permisos granulares de una app (como iOS entitlements)."""
    LEER_PIZARRA = auto()
    ESCRIBIR_PIZARRA = auto()
    MOTOR_PENSAR = auto()        # Puede invocar motor.pensar()
    BUS_PERCEPCION = auto()      # Puede usar sensores
    IPC_ENVIAR = auto()          # Puede enviar mensajes IPC
    IPC_RECIBIR = auto()         # Puede recibir mensajes IPC
    CRON = auto()                # Puede programar ejecuciones
    API_EXTERNA = auto()         # Puede llamar APIs externas
    WEBHOOK = auto()             # Puede recibir webhooks
    CR1_FRENAR = auto()          # Puede frenar el circuito (solo propietario)

    # Paquetes comunes
    BASICO = LEER_PIZARRA | MOTOR_PENSAR | BUS_PERCEPCION
    STANDARD = BASICO | ESCRIBIR_PIZARRA | IPC_ENVIAR | IPC_RECIBIR
    COMPLETO = STANDARD | CRON | API_EXTERNA | WEBHOOK
    ADMIN = COMPLETO | CR1_FRENAR


@dataclass
class Sandbox:
    """Sandbox de una app — aislamiento total.

    Una app solo puede acceder a lo que sus entitlements permiten.
    El sandbox verifica CADA operacion antes de ejecutarla.
    """
    app_id: str
    tenant_id: str
    entitlements: Entitlement
    tipos_pizarra_permitidos: list[str] = field(
        default_factory=lambda: ["estado", "cognitiva", "dominio", "temporal",
                                 "modelos", "evolucion", "interfaz", "identidad"])
    apis_externas_permitidas: list[str] = field(default_factory=list)
    operaciones_bloqueadas: int = 0

    def verificar(self, entitlement: Entitlement) -> bool:
        """Verifica si la app tiene el entitlement requerido."""
        tiene = entitlement in self.entitlements
        if not tiene:
            self.operaciones_bloqueadas += 1
            log.warning("sandbox.bloqueado",
                        app=self.app_id,
                        entitlement=str(entitlement),
                        bloqueados=self.operaciones_bloqueadas)
        return tiene

    def puede_acceder_pizarra(self, tipo: str, escritura: bool = False) -> bool:
        if tipo not in self.tipos_pizarra_permitidos:
            return False
        if escritura:
            return self.verificar(Entitlement.ESCRIBIR_PIZARRA)
        return self.verificar(Entitlement.LEER_PIZARRA)


# ============================================================
# 2. INTENTS (Android)
# ============================================================

@dataclass
class Intent:
    """Mensaje tipado para interop entre apps (Android pattern).

    El remitente no necesita saber quien es el receptor.
    El OS ruta al app mas capaz.
    """
    action: str                # "diagnosticar", "prescribir", "resumir"
    data_type: str             # "negocio", "documento", "caso_clinico"
    origen: str = ""           # App que emitio el intent
    payload: dict = field(default_factory=dict)
    requiere_respuesta: bool = True
    # Resultado (rellenado por el receptor)
    resultado: Any = None
    receptor: str = ""         # App que proceso el intent
    procesado: bool = False


class IntentRouter:
    """Router de intents — conecta apps sin acoplamiento directo.

    Cada app declara que intents puede manejar.
    El router encuentra la mejor app para cada intent.
    """

    def __init__(self):
        # {action: [{app_id, data_types, prioridad}]}
        self._handlers: dict[str, list[dict]] = {}

    def registrar_handler(self, app_id: str, action: str,
                          data_types: list[str], prioridad: int = 5):
        """Una app declara que puede manejar un tipo de intent."""
        self._handlers.setdefault(action, []).append({
            "app_id": app_id,
            "data_types": data_types,
            "prioridad": prioridad,
        })
        # Ordenar por prioridad
        self._handlers[action].sort(key=lambda h: h["prioridad"])

    def resolver(self, intent: Intent) -> list[str]:
        """Encuentra apps capaces de manejar el intent."""
        handlers = self._handlers.get(intent.action, [])
        return [
            h["app_id"] for h in handlers
            if intent.data_type in h["data_types"] or "*" in h["data_types"]
        ]

    def listar_actions(self) -> list[str]:
        return list(self._handlers.keys())


# ============================================================
# 3. DURABLE OBJECTS (Cloudflare)
# ============================================================

@dataclass
class DurableObject:
    """Agente con identidad global + storage integrado.

    Cada exocortex ES un Durable Object:
      - Identidad unica global (tenant_id + app_id)
      - Memoria persistente integrada (pizarras)
      - Activacion on-demand, sleep automatico
      - Consistencia transaccional sobre su propio estado
    """
    id: str                      # Identidad global unica
    tenant_id: str
    app_id: str
    activo: bool = False
    storage: dict = field(default_factory=dict)  # Memoria local rapida
    alarmas: list[dict] = field(default_factory=list)
    ultimo_acceso: float = 0.0

    def activar(self):
        """Despierta el objeto (on-demand)."""
        self.activo = True
        import time
        self.ultimo_acceso = time.time()

    def dormir(self):
        """Duerme el objeto (ahorra recursos)."""
        self.activo = False

    def get(self, key: str) -> Any:
        """Lee del storage local (ultra-rapido, sin DB)."""
        return self.storage.get(key)

    def put(self, key: str, value: Any):
        """Escribe en storage local."""
        self.storage[key] = value
        import time
        self.ultimo_acceso = time.time()

    def programar_alarma(self, nombre: str, cuando: str, payload: dict = None):
        """Programa una alarma futura (como alarm() de DO)."""
        self.alarmas.append({
            "nombre": nombre,
            "cuando": cuando,
            "payload": payload or {},
        })


# ============================================================
# 4. HOOKS — ACTIONS + FILTERS (WordPress)
# ============================================================

@dataclass
class Hook:
    """Un hook registrado por una app."""
    app_id: str
    nombre: str          # "before_response", "after_tool_call"
    callback: Callable
    prioridad: int = 10  # Menor = ejecuta primero
    tipo: str = "action" # "action" o "filter"


class SistemaHooks:
    """Sistema de hooks (WordPress pattern).

    Actions: ejecutan codigo en puntos especificos (fire-and-forget).
    Filters: transforman datos en transito (pipeline).

    Puntos de hook disponibles:
      before_response    — Antes de devolver respuesta al usuario
      after_response     — Despues de devolver respuesta
      before_pensar      — Antes de llamar motor.pensar()
      after_pensar       — Despues de motor.pensar()
      before_pizarra_write — Antes de escribir en pizarra
      after_ciclo        — Despues de un ciclo de NodoVivo
      on_error           — Cuando ocurre un error
      on_prescripcion    — Cuando se genera una prescripcion
    """

    def __init__(self):
        self._hooks: dict[str, list[Hook]] = {}

    def add_action(self, nombre: str, app_id: str,
                   callback: Callable, prioridad: int = 10):
        """Registra una action (fire-and-forget)."""
        self._registrar(nombre, app_id, callback, prioridad, "action")

    def add_filter(self, nombre: str, app_id: str,
                   callback: Callable, prioridad: int = 10):
        """Registra un filter (transforma datos en pipeline)."""
        self._registrar(nombre, app_id, callback, prioridad, "filter")

    def _registrar(self, nombre, app_id, callback, prioridad, tipo):
        hook = Hook(app_id=app_id, nombre=nombre,
                    callback=callback, prioridad=prioridad, tipo=tipo)
        self._hooks.setdefault(nombre, []).append(hook)
        self._hooks[nombre].sort(key=lambda h: h.prioridad)

    def do_action(self, nombre: str, *args, **kwargs):
        """Ejecuta todas las actions registradas en un hook."""
        for hook in self._hooks.get(nombre, []):
            if hook.tipo != "action":
                continue
            try:
                hook.callback(*args, **kwargs)
            except Exception as e:
                log.warning("hook.action_error",
                            nombre=nombre, app=hook.app_id,
                            error=str(e)[:80])

    def apply_filters(self, nombre: str, valor: Any, *args) -> Any:
        """Aplica filters en pipeline: cada filter recibe y devuelve valor."""
        for hook in self._hooks.get(nombre, []):
            if hook.tipo != "filter":
                continue
            try:
                valor = hook.callback(valor, *args)
            except Exception as e:
                log.warning("hook.filter_error",
                            nombre=nombre, app=hook.app_id,
                            error=str(e)[:80])
        return valor

    def remover(self, nombre: str, app_id: str):
        """Remueve todos los hooks de una app en un punto."""
        if nombre in self._hooks:
            self._hooks[nombre] = [
                h for h in self._hooks[nombre] if h.app_id != app_id]


# ============================================================
# 5. ACTIVATION EVENTS (VSCode)
# ============================================================

class TipoActivacion(str):
    """Tipos de evento que activan una app."""
    ON_TOPIC = "onTopic"        # onTopic:finanzas
    ON_SCHEDULE = "onSchedule"  # onSchedule:lunes-9am
    ON_EVENT = "onEvent"        # onEvent:nuevo_cliente
    ON_MENTION = "onMention"    # onMention:@legal
    ON_STARTUP = "onStartup"    # Al arrancar el OS
    ON_INTENT = "onIntent"      # onIntent:diagnosticar
    MANUAL = "manual"           # Solo activacion explicita


@dataclass
class ReglasActivacion:
    """Reglas de cuando activar una app (como VSCode activation events)."""
    app_id: str
    eventos: list[dict] = field(default_factory=list)
    # Cada evento: {"tipo": "onTopic", "valor": "finanzas"}

    def debe_activar(self, contexto: dict) -> bool:
        """Verifica si el contexto actual activa esta app."""
        for evento in self.eventos:
            tipo = evento.get("tipo", "")
            valor = evento.get("valor", "")

            if tipo == "onStartup":
                return True

            if tipo == "onTopic" and valor in contexto.get("topics", []):
                return True

            if tipo == "onEvent" and valor == contexto.get("evento", ""):
                return True

            if tipo == "onMention" and valor in contexto.get("menciones", []):
                return True

            if tipo == "onIntent" and valor == contexto.get("intent_action", ""):
                return True

            if tipo == "onSchedule":
                # Verificar si la hora actual coincide con el schedule
                hora_actual = contexto.get("hora", "")
                if valor == hora_actual:
                    return True

        return False


class GestorActivacion:
    """Gestor de activation events para todas las apps."""

    def __init__(self):
        self._reglas: dict[str, ReglasActivacion] = {}

    def registrar(self, reglas: ReglasActivacion):
        self._reglas[reglas.app_id] = reglas

    def apps_a_activar(self, contexto: dict) -> list[str]:
        """Dado un contexto, que apps deben activarse?"""
        return [
            app_id for app_id, reglas in self._reglas.items()
            if reglas.debe_activar(contexto)
        ]
