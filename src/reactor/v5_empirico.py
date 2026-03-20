"""Reactor v5 como código — Genera datos empíricos ACD automatizados.

Toma un caso en texto natural → ejecuta pipeline diagnóstico completo
→ produce dataset de entrenamiento para el Gestor.

Equivale a lo que se hizo manualmente en results/reactor_v5/
(50 pares × 7 dominios × 10 arquetipos × 210 datos 3L).

Maestro V4 §8.2.
"""
from __future__ import annotations

import json
import time
import structlog
from dataclasses import dataclass, field

log = structlog.get_logger()


@dataclass
class CasoReactor:
    """Un caso para el Reactor v5."""
    dominio: str
    descripcion: str
    arquetipo_esperado: str | None = None


@dataclass
class ResultadoReactor:
    """Output de un caso procesado por el Reactor v5."""
    caso: CasoReactor
    vector_funcional: dict          # {F1: x, F2: x, ...}
    lentes: dict                    # {S: x, Se: x, C: x}
    estado: str                     # "operador_ciego", "E3", etc.
    repertorio: dict                # {ints_activas, ps, rs}
    prescripcion: dict | None       # si es desequilibrado
    tiempo_s: float = 0.0
    coste_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            'dominio': self.caso.dominio,
            'descripcion': self.caso.descripcion[:200],
            'arquetipo_esperado': self.caso.arquetipo_esperado,
            'vector': self.vector_funcional,
            'lentes': self.lentes,
            'estado': self.estado,
            'repertorio': self.repertorio,
            'prescripcion': self.prescripcion,
            'tiempo_s': self.tiempo_s,
            'coste_usd': self.coste_usd,
        }


# Casos semilla por dominio (expandible)
CASOS_SEMILLA: list[CasoReactor] = [
    CasoReactor("pilates", "Estudio de Pilates reformer premium con 8 años de operación. Factura 12K/mes, 85% ocupación. Altamente dependiente de la dueña-instructora. Sin manual de operaciones, sin plan de sustitución, sin sistema de formación de instructores. Identidad clara pero atada a una persona.", "genio_mortal"),
    CasoReactor("saas", "SaaS B2B de gestión de inventario. 200 clientes, MRR 45K, churn 4% mensual. Equipo de 8 personas. El CTO escribe el 60% del código. No hay documentación técnica. Roadmap cambia cada sprint. Los clientes grandes piden custom features.", "operador_ciego"),
    CasoReactor("restauracion", "Restaurante familiar 30 años en zona turística. 3 generaciones. Recetas del abuelo. Terraza con vistas. TripAdvisor 4.8. No aceptan reservas online. El menú no ha cambiado en 5 años. Los hijos no quieren seguir.", "zombi_inmortal"),
    CasoReactor("clinica", "Clínica dental 15 profesionales. Factura 80K/mes. ISO 9001. Protocolos escritos para todo. 3 sedes. El director revisa cada presupuesto de más de 500€. No delega decisiones clínicas. Los asociados se van a los 2 años.", "automata_eterno"),
    CasoReactor("educacion", "Academia de idiomas online. 2000 alumnos activos. Modelo freemium. El fundador da clases en YouTube con 500K suscriptores. La plataforma la mantiene un freelance. No hay equipo pedagógico. El contenido lo genera el fundador solo.", "genio_mortal"),
]


async def procesar_caso(caso: CasoReactor) -> ResultadoReactor:
    """Procesa un caso con el pipeline ACD completo.

    Usa: evaluador_funcional → diagnosticar() → prescribir().
    """
    t0 = time.time()
    coste = 0.0

    # 1. Evaluar vector funcional (LLM call)
    from src.tcf.evaluador_funcional import evaluar_funcional
    vector_result = await evaluar_funcional(caso.descripcion)
    vector = vector_result.vector
    coste += vector_result.coste_usd

    # 2. Diagnosticar
    from src.tcf.diagnostico import diagnosticar
    diag = await diagnosticar(caso.descripcion)
    coste += diag.coste_usd

    # 3. Prescribir (si desequilibrado)
    prescripcion_dict = None
    if diag.estado.tipo == 'desequilibrado':
        from src.tcf.prescriptor import prescribir
        presc = prescribir(diag)
        prescripcion_dict = {
            'ints': presc.ints, 'ps': presc.ps, 'rs': presc.rs,
            'secuencia': presc.secuencia, 'frenar': presc.frenar,
            'lente_objetivo': presc.lente_objetivo,
            'modos': presc.nivel_logico.modos if presc.nivel_logico else [],
            'objetivo': presc.objetivo,
        }

    dt = time.time() - t0

    return ResultadoReactor(
        caso=caso,
        vector_funcional=vector.to_dict(),
        lentes=diag.estado_campo.lentes,
        estado=diag.estado.id,
        repertorio={
            'ints_activas': diag.repertorio.ints_activas if diag.repertorio else [],
            'ints_atrofiadas': diag.repertorio.ints_atrofiadas if diag.repertorio else [],
            'ps_activos': diag.repertorio.ps_activos if diag.repertorio else [],
            'rs_activos': diag.repertorio.rs_activos if diag.repertorio else [],
        },
        prescripcion=prescripcion_dict,
        tiempo_s=round(dt, 1),
        coste_usd=round(coste, 4),
    )


async def run(casos: list[CasoReactor] | None = None) -> dict:
    """Ejecuta el Reactor v5 sobre una lista de casos.

    Si no se pasan casos, usa CASOS_SEMILLA.
    """
    if casos is None:
        casos = CASOS_SEMILLA

    resultados = []
    total_coste = 0.0
    total_tiempo = 0.0

    for caso in casos:
        try:
            r = await procesar_caso(caso)
            resultados.append(r.to_dict())
            total_coste += r.coste_usd
            total_tiempo += r.tiempo_s
            log.info("reactor_v5_caso_ok",
                     dominio=caso.dominio, estado=r.estado,
                     tiempo=r.tiempo_s, coste=r.coste_usd)
        except Exception as e:
            log.error("reactor_v5_caso_error",
                      dominio=caso.dominio, error=str(e))
            resultados.append({
                'dominio': caso.dominio,
                'error': str(e),
            })

    return {
        'n_casos': len(casos),
        'n_ok': len([r for r in resultados if 'error' not in r]),
        'coste_total': round(total_coste, 4),
        'tiempo_total': round(total_tiempo, 1),
        'resultados': resultados,
    }
