"""Capa 2: Grafo + algoritmo óptimo (NetworkX). Código puro, $0."""
import networkx as nx
from dataclasses import dataclass, field


@dataclass
class Operacion:
    tipo: str  # 'individual', 'composicion', 'fusion'
    inteligencias: list[str]  # 1 para individual, 2 para composición/fusión
    orden: int  # secuencia de ejecución
    pasadas: int  # 1 o 2
    direccion: str | None = None  # 'INT-01→INT-08' para composiciones


@dataclass
class Algoritmo:
    inteligencias: list[str]
    operaciones: list[Operacion]
    loops: dict[str, int]  # {INT-XX: num_pasadas}
    paralelizable: list[list[str]]  # grupos ejecutables en paralelo


def componer(inteligencias: list[str], aristas: list[dict], modo: str) -> Algoritmo:
    """Genera algoritmo óptimo desde inteligencias + grafo de aristas."""

    G = nx.DiGraph()

    # 1. Construir subgrafo con inteligencias seleccionadas
    for a in aristas:
        if a['origen'] in inteligencias and a['destino'] in inteligencias:
            G.add_edge(a['origen'], a['destino'],
                       tipo=a['tipo'], peso=a['peso'],
                       direccion=a.get('direccion_optima'),
                       emergente=a.get('hallazgo_emergente'))

    operaciones: list[Operacion] = []
    orden = 0

    # 2. Identificar pares de alto diferencial para componer
    composiciones = [
        (a['origen'], a['destino'], a['peso'], a.get('direccion_optima'))
        for a in aristas
        if a['tipo'] in ('composicion', 'diferencial')
        and a['origen'] in inteligencias
        and a['destino'] in inteligencias
        and a['peso'] >= 0.85
    ]
    composiciones.sort(key=lambda x: x[2], reverse=True)

    # 3. Identificar pares para fusionar
    fusiones = [
        (a['origen'], a['destino'], a['peso'])
        for a in aristas
        if a['tipo'] == 'fusion'
        and a['origen'] in inteligencias
        and a['destino'] in inteligencias
    ]

    usadas: set[str] = set()

    # 4. Regla 4: Formal primero en composiciones
    for origen, destino, peso, direccion in composiciones[:2]:  # Max 2 composiciones
        if origen in usadas and destino in usadas:
            continue
        operaciones.append(Operacion(
            tipo='composicion',
            inteligencias=[origen, destino],
            orden=orden,
            pasadas=2 if modo in ('analisis', 'confrontacion') else 1,
            direccion=direccion or f'{origen}→{destino}'
        ))
        usadas.add(origen)
        usadas.add(destino)
        orden += 1

    # 5. Fusiones para pares no usados en composición
    for origen, destino, peso in fusiones:
        if origen in usadas or destino in usadas:
            continue
        operaciones.append(Operacion(
            tipo='fusion',
            inteligencias=[origen, destino],
            orden=orden,
            pasadas=1
        ))
        usadas.add(origen)
        usadas.add(destino)
        orden += 1

    # 6. Individuales para las que sobran
    for intel in inteligencias:
        if intel not in usadas:
            operaciones.append(Operacion(
                tipo='individual',
                inteligencias=[intel],
                orden=orden,
                pasadas=2 if modo in ('analisis', 'confrontacion') else 1
            ))
            usadas.add(intel)
            orden += 1

    # 7. Loops
    loops: dict[str, int] = {}
    for op in operaciones:
        for intel in op.inteligencias:
            loops[intel] = op.pasadas

    # 8. Paralelización (Regla 9: fusiones paralelizables ~70%)
    paralelos: list[list[str]] = []
    independientes = [op for op in operaciones if op.tipo == 'individual']
    if len(independientes) >= 2:
        paralelos.append([op.inteligencias[0] for op in independientes])

    return Algoritmo(
        inteligencias=inteligencias,
        operaciones=operaciones,
        loops=loops,
        paralelizable=paralelos
    )


async def compose(inteligencias: list[str], modo: str, aristas: list[dict] | None = None) -> Algoritmo:
    """Genera algoritmo óptimo para las inteligencias dadas."""
    if aristas is None:
        from src.db.client import fetch_aristas
        aristas = await fetch_aristas()
    return componer(inteligencias, aristas, modo)
