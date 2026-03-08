"""Capa 0: Detector de huecos sintácticos. Código puro, $0."""
import re
from dataclasses import dataclass, field


@dataclass
class Hueco:
    tipo: str           # 'verbo_sin_objeto', 'creencia_sin_evidencia', etc.
    operacion: str      # qué operación sintáctica falta
    fragmento: str      # el fragmento del input que lo evidencia
    capa: str           # a qué capa del sistema afecta
    inteligencia_sugerida: str | None = None  # qué INT activar


@dataclass
class DetectorResult:
    huecos: list[Hueco]
    perfil_acoples: dict[str, int]  # {Y: 3, PERO: 2, ...}
    diagnostico_acople: str         # "dominado por condicionales = rígido"
    inteligencias_sugeridas: list[str]  # INTs sugeridas por los huecos


# Mapeo operación → inteligencias relevantes
OPERACION_TO_INT = {
    'transitividad': ['INT-03', 'INT-05'],      # verbo sin objeto → estructural/estratégica
    'subordinacion_causal': ['INT-01', 'INT-02'], # sin porque → cuantitativa
    'subordinacion_condicional': ['INT-07', 'INT-13'],  # sin si → financiera/prospectiva
    'cuantificacion': ['INT-01', 'INT-07'],       # sin cuánto → cuantitativa
    'modificacion': ['INT-15', 'INT-09'],         # sin cualificación → estética/lingüística
    'conexion': ['INT-08', 'INT-06'],             # acoples ocultos → social/política
    'predicacion': ['INT-16', 'INT-05'],          # estado sin acción → constructiva/estratégica
    'transformacion': ['INT-14', 'INT-12'],       # categorías fijas → divergente/narrativa
}

# Conjunciones y sus patrones
CONJUNCIONES = {
    'y': 'Y', 'e': 'Y',
    'pero': 'PERO', 'sin embargo': 'PERO', 'no obstante': 'PERO',
    'aunque': 'AUNQUE', 'a pesar de': 'AUNQUE',
    'porque': 'PORQUE', 'ya que': 'PORQUE', 'dado que': 'PORQUE',
    'si': 'SI', 'en caso de': 'SI',
    'para': 'PARA', 'con el fin de': 'PARA', 'a fin de': 'PARA',
}


def detectar_huecos(input_text: str, marco: dict) -> DetectorResult:
    """Detecta huecos sintácticos en el input. Código puro."""
    huecos = []

    oraciones = re.split(r'[.!?]+', input_text)
    oraciones = [o.strip() for o in oraciones if o.strip()]

    for oracion in oraciones:
        palabras = oracion.lower().split()

        # 1. Transitividad: verbos sin objeto claro
        verbos_transitivos = ['quiere', 'busca', 'necesita', 'planea', 'considera',
                              'piensa', 'decide', 'elige', 'lidera', 'gestiona', 'dirige']
        for verbo in verbos_transitivos:
            if verbo in palabras:
                idx = palabras.index(verbo)
                # Si el verbo está al final o seguido de punto/conjunción
                if idx >= len(palabras) - 2:
                    huecos.append(Hueco(
                        tipo='verbo_sin_objeto',
                        operacion='transitividad',
                        fragmento=oracion,
                        capa='funciones',
                        inteligencia_sugerida='INT-03'
                    ))

        # 2. Cuantificación ausente: magnitudes sin número
        cuant_vagas = ['mucho', 'poco', 'bastante', 'algo', 'varios', 'algunos']
        for vago in cuant_vagas:
            if vago in palabras:
                huecos.append(Hueco(
                    tipo='cuantificacion_vaga',
                    operacion='cuantificacion',
                    fragmento=oracion,
                    capa='lentes',
                    inteligencia_sugerida='INT-01'
                ))
                break

    # 4. Perfil de acoples (análisis global del input)
    text_lower = input_text.lower()
    perfil: dict[str, int] = {}
    for patron, tipo in CONJUNCIONES.items():
        count = text_lower.count(patron)
        if count > 0:
            perfil[tipo] = perfil.get(tipo, 0) + count

    # 5. Diagnóstico por perfil de acoples
    diagnostico = diagnosticar_perfil(perfil)

    # 6. Subordinación causal ausente
    tiene_porque = any(c in text_lower for c in ['porque', 'ya que', 'dado que', 'debido a'])
    if not tiene_porque and len(oraciones) >= 2:
        huecos.append(Hueco(
            tipo='sin_causalidad',
            operacion='subordinacion_causal',
            fragmento='(input completo)',
            capa='creencias',
            inteligencia_sugerida='INT-01'
        ))

    # 7. Finalidad ausente
    tiene_para = any(c in text_lower for c in ['para', 'con el fin de', 'a fin de'])
    if not tiene_para and len(oraciones) >= 1:
        huecos.append(Hueco(
            tipo='sin_finalidad',
            operacion='subordinacion_final',
            fragmento='(input completo)',
            capa='reglas',
            inteligencia_sugerida='INT-17'
        ))

    # 8. Recoger inteligencias sugeridas (dedup, ordenadas por frecuencia)
    sugeridas: dict[str, int] = {}
    for h in huecos:
        if h.inteligencia_sugerida:
            sugeridas[h.inteligencia_sugerida] = sugeridas.get(h.inteligencia_sugerida, 0) + 1
        if h.operacion in OPERACION_TO_INT:
            for int_id in OPERACION_TO_INT[h.operacion]:
                sugeridas[int_id] = sugeridas.get(int_id, 0) + 1

    inteligencias_sugeridas = sorted(sugeridas.keys(), key=lambda k: sugeridas[k], reverse=True)

    return DetectorResult(
        huecos=huecos,
        perfil_acoples=perfil,
        diagnostico_acople=diagnostico,
        inteligencias_sugeridas=inteligencias_sugeridas[:5]
    )


def diagnosticar_perfil(perfil: dict[str, int]) -> str:
    """Diagnóstico basado en el perfil de acoples."""
    total = sum(perfil.values())
    if total == 0:
        return "Sin acoples explícitos — relaciones implícitas no verificadas"

    dominante = max(perfil, key=perfil.get) if perfil else None

    diagnosticos = {
        'SI': 'Dominado por condicionales — sistema rígido/frágil',
        'AUNQUE': 'Dominado por concesivas — fugas toleradas',
        'PERO': 'Dominado por tensiones — fricción activa',
        'PORQUE': 'Dominado por causales — cadena causal explícita',
        'Y': 'Dominado por sinergias — puede ocultar tensiones',
        'PARA': 'Dominado por finalidad — orientado pero puede ser rígido',
    }

    return diagnosticos.get(dominante, "Perfil mixto")


async def detect(input_text: str) -> DetectorResult:
    """Ejecuta detección de huecos. Síncrono envuelto en async para consistencia."""
    from src.meta_red import load_marco_linguistico
    marco = load_marco_linguistico()
    return detectar_huecos(input_text, marco)
