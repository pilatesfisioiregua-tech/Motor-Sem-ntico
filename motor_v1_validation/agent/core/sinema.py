"""Sinema — Singular, Existencial, Metaforico.

Patron Weakening (#60676): relajar restricciones heuristicas cuando justificado.
Patron Topological Projection (#60677): reducir dimensionalidad del problema.

Tres operaciones:
1. Weakening: relajar heuristicas del Manifold (R2,R4-R9,R11-R13)
2. Projection: reducir espacio de gaps a las 3 celdas mas relevantes
3. Relaxation: ampliar umbral de aceptacion de programas
"""

import re
from typing import Optional


# Indicadores de ambiguedad en el input
MARKERS_METAFORA = [
    'como si', 'es como', 'parece', 'seria como', 'metafora',
    'siento que', 'intuyo', 'algo me dice', 'en el fondo',
    'no se como decirlo', 'es dificil de explicar',
]

MARKERS_EXISTENCIAL = [
    'sentido', 'proposito', 'por que', 'para que', 'vale la pena',
    'tiene sentido', 'que sentido tiene', 'existencial',
    'vacio', 'direccion', 'norte', 'rumbo',
]

MARKERS_SINGULAR = [
    'unico', 'nunca antes', 'primera vez', 'sin precedentes',
    'nadie ha', 'no existe', 'inventar', 'crear desde cero',
]


class Sinema:
    """Manejo de inputs ambiguos, metaforicos y existenciales."""

    def detectar_ambiguedad(self, input_texto: str) -> float:
        """Score 0-1 de ambiguedad del input.

        Mas alto = mas ambiguo/metaforico/existencial.
        """
        text = input_texto.lower()
        score = 0.0

        # Marcadores metaforicos
        n_metafora = sum(1 for m in MARKERS_METAFORA if m in text)
        score += min(0.3, n_metafora * 0.1)

        # Marcadores existenciales
        n_existencial = sum(1 for m in MARKERS_EXISTENCIAL if m in text)
        score += min(0.3, n_existencial * 0.1)

        # Marcadores singulares
        n_singular = sum(1 for m in MARKERS_SINGULAR if m in text)
        score += min(0.2, n_singular * 0.1)

        # Longitud: inputs muy cortos o muy largos son mas ambiguos
        words = text.split()
        if len(words) < 5:
            score += 0.1
        elif len(words) > 100:
            score += 0.05

        # Preguntas sin verbo claro
        if '?' in text and not any(v in text for v in ['puedo', 'debo', 'como', 'cuando', 'donde', 'que hacer']):
            score += 0.1

        return min(1.0, score)

    def weakening(self, programa: dict, nivel: float) -> dict:
        """Relajar heuristicas proporcionalmente al nivel de ambiguedad.

        Las invariantes (R01, R03, R10) NUNCA se relajan.
        Las heuristicas se relajan proporcionalmente.
        """
        if nivel < 0.3:
            return programa  # no necesita relajacion

        prog = dict(programa)
        ints = list(prog.get('inteligencias', []))

        # R03 relaxation: permitir mas inteligencias si nivel alto
        if nivel > 0.6:
            prog['max_inteligencias'] = 7  # vs 6 normal
        if nivel > 0.8:
            prog['max_inteligencias'] = 8

        # R04 relaxation: no forzar orden formal-primero si existencial
        if nivel > 0.5 and any(m in str(programa) for m in MARKERS_EXISTENCIAL):
            prog['orden_flexible'] = True

        # R07 relaxation: no forzar loop_test en modo sinema
        if nivel > 0.7:
            prog['profundidad'] = 1  # una pasada basta para exploracion

        # Añadir inteligencias existenciales si no estan
        existenciales = {'INT-08', 'INT-17', 'INT-18'}
        if nivel > 0.5 and not existenciales.intersection(set(ints)):
            ints.append('INT-08')
            prog['inteligencias'] = ints

        prog['sinema_nivel'] = round(nivel, 2)
        prog['sinema_activo'] = True

        return prog

    def projection(self, gradientes: dict) -> dict:
        """Reducir espacio de gaps a las 3 celdas mas relevantes.

        Proyeccion topologica: de 21 celdas a 3 celdas dominantes.
        Util para inputs ambiguos donde muchas celdas tienen gap similar.
        """
        top_gaps = gradientes.get('top_gaps', [])
        if len(top_gaps) <= 3:
            return gradientes

        # Proyectar: tomar top 3 por gap, diversificando lentes
        lentes_vistas = set()
        proyectados = []

        for celda, gap in top_gaps:
            parts = celda.split('x')
            lente = parts[1] if len(parts) > 1 else ''
            if lente not in lentes_vistas and len(proyectados) < 3:
                proyectados.append((celda, gap))
                lentes_vistas.add(lente)

        # Rellenar si faltan
        for celda, gap in top_gaps:
            if len(proyectados) >= 3:
                break
            if (celda, gap) not in proyectados:
                proyectados.append((celda, gap))

        result = dict(gradientes)
        result['top_gaps'] = proyectados[:3]
        result['proyeccion_aplicada'] = True
        result['gaps_originales'] = len(top_gaps)

        return result

    def relaxation(self, programa: dict) -> dict:
        """Ampliar margenes de aceptacion para programas en modo sinema.

        En vez de rechazar programas imperfectos, ampliar tolerancias.
        """
        prog = dict(programa)

        # Ampliar presupuesto de inteligencias
        ints = prog.get('inteligencias', [])
        if len(ints) < 3:
            # Añadir inteligencias de exploración
            exploratorias = ['INT-14', 'INT-09', 'INT-08']
            for e in exploratorias:
                if e not in ints and len(ints) < 4:
                    ints.append(e)
            prog['inteligencias'] = ints

        prog['relaxation_aplicada'] = True
        return prog


# Singleton
_sinema = None

def get_sinema() -> Sinema:
    global _sinema
    if _sinema is None:
        _sinema = Sinema()
    return _sinema
