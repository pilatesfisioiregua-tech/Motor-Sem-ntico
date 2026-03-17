"""13 Reglas del Compilador como Constraint Manifold.

Patron aplicado: Compilador de Inteligencias (#60665)
Las 13 reglas definen superficies en el espacio de programas.
Un programa valido es un punto en la interseccion de todas las superficies.

Tres operaciones:
  validar()   — ¿el programa esta en la interseccion?
  proyectar() — correccion minima para llevarlo a la interseccion
  generar()   — crear programa valido por construccion

Jerarquia:
  INVARIANTES (absolutas): R01 (nucleo), R03 (presupuesto), R10 (cruce)
  HEURISTICAS (margen):    R02, R04-R09, R11-R13
"""

from dataclasses import dataclass
from typing import Optional


# Clasificacion de inteligencias
CUANTITATIVAS = {'INT-01', 'INT-02'}
HUMANAS = {'INT-08', 'INT-17'}
FORMALES = {'INT-01', 'INT-02', 'INT-03', 'INT-04', 'INT-07'}  # distantes/formales
CERCANAS = {'INT-08', 'INT-10', 'INT-17', 'INT-18'}             # humanas/cercanas
CREATIVAS = {'INT-14', 'INT-15', 'INT-09', 'INT-12', 'INT-13'}
FRONTERA = {'INT-17', 'INT-18', 'INT-06'}
CONSTRUCTIVA = {'INT-16'}

# Todas las inteligencias
ALL_INTS = {f'INT-{i:02d}' for i in range(1, 19)}


@dataclass
class RuleResult:
    """Resultado de evaluar una regla sobre un programa."""
    valido: bool
    violacion: Optional[str] = None
    correccion: Optional[dict] = None  # programa corregido si es posible
    es_invariante: bool = False         # True = no negociable


# =====================================================
# 13 REGLAS — cada una retorna RuleResult
# =====================================================

# --- SELECCION (Router) ---

def R01_nucleo_irreducible(programa: dict) -> RuleResult:
    """Siempre >=1 cuantitativa (INT-01/02) + >=1 humana (INT-08/17) + INT-16.

    INVARIANTE: no negociable.
    """
    ints = set(programa.get('inteligencias', []))
    tiene_cuant = bool(ints & CUANTITATIVAS)
    tiene_humana = bool(ints & HUMANAS)
    tiene_16 = 'INT-16' in ints

    if tiene_cuant and tiene_humana and tiene_16:
        return RuleResult(valido=True, es_invariante=True)

    # Proyeccion: añadir lo que falta
    corregido = dict(programa)
    ints_corregidas = set(ints)
    violaciones = []

    if not tiene_cuant:
        ints_corregidas.add('INT-01')  # default cuantitativa
        violaciones.append('falta cuantitativa, añadida INT-01')
    if not tiene_humana:
        ints_corregidas.add('INT-08')  # default humana
        violaciones.append('falta humana, añadida INT-08')
    if not tiene_16:
        ints_corregidas.add('INT-16')
        violaciones.append('falta INT-16, añadida')

    corregido['inteligencias'] = sorted(ints_corregidas)
    return RuleResult(
        valido=False,
        violacion=f"Nucleo irreducible incompleto: {', '.join(violaciones)}",
        correccion=corregido,
        es_invariante=True,
    )


def R02_maximo_diferencial(programa: dict) -> RuleResult:
    """Priorizar eje cuantitativo-existencial.

    El maximo diferencial se consigue combinando inteligencias
    de polos opuestos: cuantitativa + existencial, formal + creativa.
    """
    ints = set(programa.get('inteligencias', []))

    tiene_cuant = bool(ints & CUANTITATIVAS)
    tiene_existencial = bool(ints & CERCANAS)
    tiene_formal = bool(ints & FORMALES)
    tiene_creativa = bool(ints & CREATIVAS)

    # Al menos un eje de tension presente
    tiene_eje = (tiene_cuant and tiene_existencial) or (tiene_formal and tiene_creativa)

    if tiene_eje:
        return RuleResult(valido=True)

    # Sugerir añadir polo opuesto
    corregido = dict(programa)
    ints_c = set(ints)
    if tiene_cuant and not tiene_existencial:
        ints_c.add('INT-08')
    elif tiene_existencial and not tiene_cuant:
        ints_c.add('INT-01')
    elif tiene_formal and not tiene_creativa:
        ints_c.add('INT-14')
    elif tiene_creativa and not tiene_formal:
        ints_c.add('INT-01')
    else:
        ints_c.add('INT-01')
        ints_c.add('INT-08')

    corregido['inteligencias'] = sorted(ints_c)
    return RuleResult(
        valido=False,
        violacion="Sin eje cuantitativo-existencial",
        correccion=corregido,
    )


def R03_presupuesto(programa: dict) -> RuleResult:
    """4-5 inteligencias. <3 = puntos ciegos. >6 = ruido.

    INVARIANTE: 3 <= |ints| <= 6 (margen de 1 en cada lado).
    """
    ints = list(programa.get('inteligencias', []))
    n = len(ints)

    if 3 <= n <= 6:
        return RuleResult(valido=True, es_invariante=True)

    corregido = dict(programa)
    if n < 3:
        # Añadir hasta 4 usando nucleo irreducible + diferencial
        ints_set = set(ints)
        for candidata in ['INT-01', 'INT-08', 'INT-16', 'INT-14']:
            if len(ints_set) >= 4:
                break
            ints_set.add(candidata)
        corregido['inteligencias'] = sorted(ints_set)
        return RuleResult(
            valido=False,
            violacion=f"Solo {n} inteligencias (<3 = puntos ciegos). Ampliado a {len(ints_set)}.",
            correccion=corregido,
            es_invariante=True,
        )
    else:
        # Reducir a 5: mantener nucleo irreducible + las de mayor score
        ints_set = set(ints)
        nucleo = {'INT-01', 'INT-08', 'INT-16'} & ints_set
        otras = sorted(ints_set - nucleo)
        mantener = nucleo | set(otras[:5 - len(nucleo)])
        corregido['inteligencias'] = sorted(mantener)
        return RuleResult(
            valido=False,
            violacion=f"{n} inteligencias (>6 = ruido). Reducido a {len(mantener)}.",
            correccion=corregido,
            es_invariante=True,
        )


# --- ORDEN ---

def R04_formal_primero(programa: dict) -> RuleResult:
    """Formal/distante primero -> humano/cercano despues."""
    orden = list(programa.get('inteligencias', []))
    if len(orden) <= 1:
        return RuleResult(valido=True)

    # Separar en formales y cercanas
    formales = [i for i in orden if i in FORMALES]
    cercanas = [i for i in orden if i in CERCANAS]
    otras = [i for i in orden if i not in FORMALES and i not in CERCANAS]

    # Orden correcto: formales -> otras -> cercanas
    orden_correcto = formales + otras + cercanas

    if orden == orden_correcto:
        return RuleResult(valido=True)

    corregido = dict(programa)
    corregido['inteligencias'] = orden_correcto
    return RuleResult(
        valido=False,
        violacion="Orden incorrecto: humanas antes que formales",
        correccion=corregido,
    )


def R05_no_reorganizar(programa: dict) -> RuleResult:
    """Secuencia lineal (A->B)->C supera A->(B->C)."""
    operaciones = programa.get('operaciones', [])
    if not operaciones:
        return RuleResult(valido=True)

    for op in operaciones:
        if isinstance(op, dict) and op.get('tipo') == 'secuencia':
            pasos = op.get('pasos', [])
            anidadas = [p for p in pasos if isinstance(p, dict) and p.get('tipo') == 'secuencia']
            if anidadas:
                return RuleResult(
                    valido=False,
                    violacion="Secuencia anidada detectada — aplanar a lineal",
                    correccion=None,
                )

    return RuleResult(valido=True)


def R06_fusiones_cuidado(programa: dict) -> RuleResult:
    """Orden en fusiones afecta framing. Primero la mas alineada con el sujeto."""
    operaciones = programa.get('operaciones', [])
    for op in operaciones:
        if isinstance(op, dict) and op.get('tipo') == 'fusion':
            if 'orden' not in op:
                return RuleResult(
                    valido=False,
                    violacion="Fusion sin orden explicito — especificar cual va primero",
                )

    return RuleResult(valido=True)


# --- PROFUNDIDAD ---

def R07_loop_test(programa: dict) -> RuleResult:
    """2 pasadas por defecto en modo analisis/confrontacion."""
    modo = programa.get('modo', 'analisis')
    profundidad = programa.get('profundidad', 1)

    if modo in ('analisis', 'confrontacion') and profundidad < 2:
        corregido = dict(programa)
        corregido['profundidad'] = 2
        return RuleResult(
            valido=False,
            violacion=f"Modo {modo} requiere minimo 2 pasadas, tiene {profundidad}",
            correccion=corregido,
        )

    return RuleResult(valido=True)


def R08_no_tercera_pasada(programa: dict) -> RuleResult:
    """n=3 no justifica coste excepto calibracion."""
    profundidad = programa.get('profundidad', 1)
    modo = programa.get('modo', 'analisis')

    if profundidad > 2 and modo != 'calibracion':
        corregido = dict(programa)
        corregido['profundidad'] = 2
        return RuleResult(
            valido=False,
            violacion=f"Profundidad {profundidad} > 2 no justificada (modo={modo})",
            correccion=corregido,
        )

    return RuleResult(valido=True)


# --- PARALELIZACION ---

def R09_fusiones_factorizables(programa: dict) -> RuleResult:
    """A->(B|C) como (A->B)|(A->C) perdiendo ~30%. Aceptable si no TOP 5."""
    operaciones = programa.get('operaciones', [])
    for op in operaciones:
        if isinstance(op, dict) and op.get('tipo') == 'fusion' and op.get('factorizable', False):
            return RuleResult(
                valido=True,
                violacion="Fusion factorizable — perdida ~30% aceptable si no critica",
            )

    return RuleResult(valido=True)


def R10_cruce_no_factorizable(programa: dict) -> RuleResult:
    """(B|C)->A tiene valor irreducible. INVARIANTE.

    Un cruce previo (multiples inputs -> una integracion) NO se puede factorizar.
    """
    operaciones = programa.get('operaciones', [])
    for op in operaciones:
        if isinstance(op, dict) and op.get('tipo') == 'cruce':
            if op.get('factorizado', False):
                return RuleResult(
                    valido=False,
                    violacion="Cruce (B|C)->A factorizado ilegalmente — valor irreducible",
                    es_invariante=True,
                )

    return RuleResult(valido=True, es_invariante=True)


# --- PATRONES UNIVERSALES ---

def R11_marco_binario(programa: dict) -> RuleResult:
    """Primera accion: INT-14 (ampliar) + INT-01 (filtrar)."""
    ints = list(programa.get('inteligencias', []))
    if len(ints) < 2:
        return RuleResult(valido=True)

    if 'INT-14' in ints and 'INT-01' in ints:
        idx_14 = ints.index('INT-14')
        idx_01 = ints.index('INT-01')
        if idx_14 > 2 and idx_01 > 2:
            return RuleResult(
                valido=False,
                violacion="INT-14 (ampliar) e INT-01 (filtrar) deberian estar entre los primeros",
            )

    return RuleResult(valido=True)


def R12_conversacion_pendiente(programa: dict) -> RuleResult:
    """Buscar patron 'conversacion no tenida' como output minimo."""
    outputs = programa.get('outputs_esperados', [])
    if not outputs:
        return RuleResult(valido=True)

    tiene_conv = any('conversacion' in str(o).lower() for o in outputs)
    if not tiene_conv:
        return RuleResult(
            valido=False,
            violacion="Output no incluye busqueda de 'conversacion pendiente'",
        )

    return RuleResult(valido=True)


def R13_infrautilizacion(programa: dict) -> RuleResult:
    """Medir uso actual antes de construir nuevo.

    Si hay una inteligencia poco usada que podria servir,
    preferirla antes de añadir una nueva.
    """
    stats = programa.get('stats_uso', {})
    if not stats:
        return RuleResult(valido=True)

    ints = set(programa.get('inteligencias', []))
    infrautilizadas = {k for k, v in stats.items()
                       if v.get('uso_pct', 100) < 20 and k in ALL_INTS}

    candidatas = infrautilizadas - ints
    if candidatas and len(ints) >= 4:
        return RuleResult(
            valido=False,
            violacion=f"Inteligencias infrautilizadas disponibles: {candidatas}",
        )

    return RuleResult(valido=True)


# =====================================================
# CONSTRAINT MANIFOLD — 3 operaciones
# =====================================================

class ConstraintManifold:
    """13 reglas como variedad de restriccion en espacio de programas.

    Tres operaciones:
      validar()   — ¿p esta en la interseccion de todas las superficies?
      proyectar() — proyeccion al punto mas cercano dentro de la variedad
      generar()   — muestrear punto valido por construccion
    """

    def __init__(self):
        # Invariantes (absolutas, no negociables)
        self.invariants = [
            ('R01', R01_nucleo_irreducible),
            ('R03', R03_presupuesto),
            ('R10', R10_cruce_no_factorizable),
        ]
        # Heuristicas (con margen)
        self.heuristics = [
            ('R02', R02_maximo_diferencial),
            ('R04', R04_formal_primero),
            ('R05', R05_no_reorganizar),
            ('R06', R06_fusiones_cuidado),
            ('R07', R07_loop_test),
            ('R08', R08_no_tercera_pasada),
            ('R09', R09_fusiones_factorizables),
            ('R11', R11_marco_binario),
            ('R12', R12_conversacion_pendiente),
            ('R13', R13_infrautilizacion),
        ]

    def validar(self, programa: dict) -> tuple:
        """Validar programa contra todas las reglas.

        Returns:
            (bool, list[dict]) — (valido, violaciones)
        """
        violaciones = []
        valido_global = True

        for nombre, regla in self.invariants + self.heuristics:
            try:
                resultado = regla(programa)
                if not resultado.valido:
                    valido_global = False
                    violaciones.append({
                        'regla': nombre,
                        'violacion': resultado.violacion,
                        'es_invariante': resultado.es_invariante,
                        'tiene_correccion': resultado.correccion is not None,
                    })
            except Exception as e:
                violaciones.append({
                    'regla': nombre,
                    'violacion': f'Error evaluando regla: {str(e)}',
                    'es_invariante': False,
                })

        return (valido_global, violaciones)

    def proyectar(self, programa: dict) -> dict:
        """Proyeccion al punto mas cercano dentro de la variedad.

        Orden de proyeccion:
        1. Primero invariantes (no negociables)
        2. Luego heuristicas (minima perturbacion)
        """
        p = dict(programa)

        # 1. Proyectar invariantes primero
        for nombre, regla in self.invariants:
            try:
                resultado = regla(p)
                if not resultado.valido and resultado.correccion:
                    p = resultado.correccion
            except Exception:
                pass

        # 2. Proyectar heuristicas
        for nombre, regla in self.heuristics:
            try:
                resultado = regla(p)
                if not resultado.valido and resultado.correccion:
                    p = resultado.correccion
            except Exception:
                pass

        return p

    def generar(self, gradientes: dict, modo: str = 'analisis') -> dict:
        """Generar programa valido por construccion.

        Usa gradientes para guiar seleccion de INTs,
        luego aplica reglas como restricciones constructivas.
        Criticality-aware: uses adjusted bounds from CriticalityEngine.

        Args:
            gradientes: dict con top_gaps (del campo de gradientes)
            modo: analisis|conversacion|generacion|confrontacion

        Returns:
            dict programa valido que satisface todas las reglas
        """
        top_gaps = gradientes.get('top_gaps', [])
        max_ints = getattr(self, '_criticality_max_ints', 6)
        crit_profundidad = getattr(self, '_criticality_profundidad', None)

        # Paso 1: Seleccionar inteligencias segun modo
        if modo == 'conversacion':
            n_target = 3
        elif modo in ('generacion', 'confrontacion'):
            n_target = 4
        else:  # analisis
            n_target = min(5, max_ints)

        # Paso 2: Nucleo irreducible (R01)
        ints = set()
        ints.add('INT-01')  # cuantitativa
        ints.add('INT-08')  # humana
        ints.add('INT-16')  # constructiva

        # Paso 3: Añadir por modo
        if modo == 'generacion':
            for candidata in ['INT-14', 'INT-15', 'INT-09']:
                if len(ints) < n_target:
                    ints.add(candidata)
        elif modo == 'confrontacion':
            for candidata in ['INT-17', 'INT-18', 'INT-06']:
                if len(ints) < n_target:
                    ints.add(candidata)
        else:
            # Seleccionar por gaps (las inteligencias mas relevantes para los gaps detectados)
            gap_ints = _ints_para_gaps(top_gaps)
            for candidata in gap_ints:
                if len(ints) < n_target:
                    ints.add(candidata)

        # Paso 4: Maximo diferencial (R02) — asegurar tension
        if not (ints & CREATIVAS) and not (ints & FRONTERA):
            ints.add('INT-14')  # añadir polo creativo

        # Paso 5: Presupuesto (R03) — ajustar a 3-max_ints (criticality-aware)
        ints_lista = sorted(ints)
        if len(ints_lista) > max_ints:
            nucleo = {'INT-01', 'INT-08', 'INT-16'}
            otras = [i for i in ints_lista if i not in nucleo]
            ints_lista = sorted(nucleo) + otras[:max_ints - len(nucleo)]

        # Paso 6: Orden (R04) — formal primero (skip if criticality says flexible)
        orden_flexible = getattr(self, '_criticality_orden_flexible', False)
        if not orden_flexible:
            formales = [i for i in ints_lista if i in FORMALES]
            cercanas_l = [i for i in ints_lista if i in CERCANAS]
            otras_l = [i for i in ints_lista if i not in FORMALES and i not in CERCANAS]
            ints_ordenadas = formales + otras_l + cercanas_l
        else:
            ints_ordenadas = ints_lista

        # Paso 7: Profundidad (R07/R08) — criticality-aware
        if crit_profundidad is not None:
            profundidad = crit_profundidad
        elif modo in ('analisis', 'confrontacion'):
            profundidad = 2
        else:
            profundidad = 1

        programa = {
            'inteligencias': ints_ordenadas,
            'modo': modo,
            'profundidad': profundidad,
            'operaciones': [],
            'n_inteligencias': len(ints_ordenadas),
        }

        return programa


def _ints_para_gaps(top_gaps: list) -> list:
    """Mapear gaps (celda = FuncionxLente) a inteligencias relevantes."""
    mapping_funcion = {
        'Conservar': ['INT-07', 'INT-05'],
        'Captar': ['INT-02', 'INT-06'],
        'Depurar': ['INT-03', 'INT-04'],
        'Distribuir': ['INT-05', 'INT-07'],
        'Frontera': ['INT-06', 'INT-17'],
        'Adaptar': ['INT-09', 'INT-14'],
        'Replicar': ['INT-12', 'INT-13'],
    }

    resultado = []
    for celda, gap in top_gaps[:5]:
        if not isinstance(celda, str) or 'x' not in celda:
            continue
        funcion = celda.split('x')[0]
        candidatas = mapping_funcion.get(funcion, [])
        for c in candidatas:
            if c not in resultado:
                resultado.append(c)

    return resultado


# Instancia global del manifold
_manifold = None

def get_manifold(apply_criticality: bool = True) -> ConstraintManifold:
    """Obtener instancia singleton del Constraint Manifold.

    If apply_criticality=True, adjusts R03 bounds and R07 depth
    based on CriticalityEngine temperature regime.
    """
    global _manifold
    if _manifold is None:
        _manifold = ConstraintManifold()

    if apply_criticality:
        try:
            from .criticality_engine import get_criticality_engine
            crit = get_criticality_engine()
            ajuste = crit.ajustar_manifold_temperatura()
            # Dynamically patch R03 bounds based on regime
            max_ints = ajuste.get('R03_max_ints', 6)
            _manifold._criticality_max_ints = max_ints
            _manifold._criticality_profundidad = ajuste.get('R07_profundidad', 2)
            _manifold._criticality_orden_flexible = ajuste.get('R04_orden_flexible', False)
        except Exception:
            pass  # Criticality never breaks compilation

    return _manifold
