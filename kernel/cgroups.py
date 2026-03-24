"""cgroups + namespaces — aislamiento y gobernanza de recursos (Linux).

cgroups: Limites de recursos por agente (tokens, queries, profundidad compose).
namespaces: Aislamiento semantico (cada agente ve solo su slice de datos).

Evita que un agente descontrolado consuma todos los recursos del sistema.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from typing import Optional

log = structlog.get_logger()


@dataclass
class LimitesRecurso:
    """Limites de recursos para un cgroup."""
    tokens_por_ciclo: int = 50_000         # Max tokens LLM por ciclo
    queries_por_minuto: int = 100          # Max queries DB por minuto
    compose_depth: int = 5                 # Max profundidad de composicion
    memoria_kb: int = 10_000               # Max filas en pizarra del agente
    coste_por_ciclo_usd: float = 0.50      # Max coste LLM por ciclo
    timeout_operacion_seg: float = 30.0    # Max tiempo por operacion


@dataclass
class UsoRecurso:
    """Uso actual de recursos de un cgroup."""
    tokens_usados: int = 0
    queries_realizadas: int = 0
    compose_depth_actual: int = 0
    memoria_usada_kb: int = 0
    coste_ciclo_usd: float = 0.0

    def reset_ciclo(self):
        """Reset al inicio de cada ciclo."""
        self.tokens_usados = 0
        self.queries_realizadas = 0
        self.compose_depth_actual = 0
        self.coste_ciclo_usd = 0.0


@dataclass
class Cgroup:
    """Control group para un agente o grupo de agentes.

    Mete y controla el consumo de recursos. Si se excede un limite,
    la operacion se rechaza (no se mata el agente, solo se frena).
    """
    nombre: str
    limites: LimitesRecurso = field(default_factory=LimitesRecurso)
    uso: UsoRecurso = field(default_factory=UsoRecurso)
    prioridad: int = 5              # 1=critico (como nice en Linux)
    throttled: bool = False          # Si True, esta frenado por exceso

    def puede_usar_tokens(self, n: int) -> bool:
        """Verifica si puede consumir N tokens mas."""
        return self.uso.tokens_usados + n <= self.limites.tokens_por_ciclo

    def puede_query(self) -> bool:
        return self.uso.queries_realizadas < self.limites.queries_por_minuto

    def puede_compose(self, depth: int) -> bool:
        return depth <= self.limites.compose_depth

    def puede_gastar(self, coste: float) -> bool:
        return self.uso.coste_ciclo_usd + coste <= self.limites.coste_por_ciclo_usd

    def registrar_tokens(self, n: int):
        self.uso.tokens_usados += n
        self._check_throttle()

    def registrar_query(self):
        self.uso.queries_realizadas += 1

    def registrar_coste(self, coste: float):
        self.uso.coste_ciclo_usd += coste
        self._check_throttle()

    def _check_throttle(self):
        if (self.uso.tokens_usados >= self.limites.tokens_por_ciclo * 0.9 or
                self.uso.coste_ciclo_usd >= self.limites.coste_por_ciclo_usd * 0.9):
            self.throttled = True
            log.warning("cgroup.throttled", nombre=self.nombre)


@dataclass
class Namespace:
    """Namespace semantico — aislamiento de vista de datos.

    Un agente en namespace 'pilates' solo ve datos con tenant_id='pilates'.
    El OS puede ver todos los namespaces (para telemetria anonimizada).
    """
    nombre: str
    tenant_id: str
    tipos_pizarra_permitidos: list[str] = field(
        default_factory=lambda: ["estado", "cognitiva", "dominio", "temporal",
                                 "modelos", "evolucion", "interfaz", "identidad"])
    solo_lectura: bool = False

    def puede_acceder(self, tipo: str, escritura: bool = False) -> bool:
        """Verifica si el namespace permite acceso a este tipo de pizarra."""
        if tipo not in self.tipos_pizarra_permitidos:
            return False
        if escritura and self.solo_lectura:
            return False
        return True


class GestorRecursos:
    """Gestor central de cgroups y namespaces.

    Crea y gestiona recursos para todos los agentes.
    Perfiles predefinidos por criticidad.
    """

    # Perfiles predefinidos
    PERFILES = {
        "critico": LimitesRecurso(
            tokens_por_ciclo=100_000,
            queries_por_minuto=200,
            compose_depth=10,
            coste_por_ciclo_usd=1.0,
        ),
        "normal": LimitesRecurso(),  # Defaults
        "background": LimitesRecurso(
            tokens_por_ciclo=10_000,
            queries_por_minuto=20,
            compose_depth=3,
            coste_por_ciclo_usd=0.10,
        ),
        "readonly": LimitesRecurso(
            tokens_por_ciclo=0,
            queries_por_minuto=50,
            compose_depth=0,
            coste_por_ciclo_usd=0.0,
        ),
    }

    def __init__(self):
        self._cgroups: dict[str, Cgroup] = {}
        self._namespaces: dict[str, Namespace] = {}

    def crear_cgroup(self, nombre: str, perfil: str = "normal",
                     prioridad: int = 5) -> Cgroup:
        """Crea un cgroup con perfil predefinido."""
        limites = self.PERFILES.get(perfil, self.PERFILES["normal"])
        cg = Cgroup(nombre=nombre, limites=limites, prioridad=prioridad)
        self._cgroups[nombre] = cg
        return cg

    def crear_namespace(self, nombre: str, tenant_id: str,
                        solo_lectura: bool = False) -> Namespace:
        """Crea un namespace para un agente."""
        ns = Namespace(nombre=nombre, tenant_id=tenant_id,
                       solo_lectura=solo_lectura)
        self._namespaces[nombre] = ns
        return ns

    def obtener_cgroup(self, nombre: str) -> Optional[Cgroup]:
        return self._cgroups.get(nombre)

    def obtener_namespace(self, nombre: str) -> Optional[Namespace]:
        return self._namespaces.get(nombre)

    def reset_ciclo_todos(self):
        """Reset de uso al inicio de cada ciclo."""
        for cg in self._cgroups.values():
            cg.uso.reset_ciclo()
            cg.throttled = False

    @property
    def stats(self) -> dict:
        throttled = [n for n, cg in self._cgroups.items() if cg.throttled]
        return {
            "cgroups": len(self._cgroups),
            "namespaces": len(self._namespaces),
            "throttled": throttled,
        }
