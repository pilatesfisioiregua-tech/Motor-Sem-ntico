"""Constantes del Reactor: dominios, pares complementarios, firmas."""

DOMINIOS: list[str] = [
    "Clínica dental / salud",
    "SaaS B2B / tecnología",
    "Restauración / hostelería",
    "Despacho legal / servicios profesionales",
    "Retail / comercio minorista",
    "Educación / formación",
    "Inmobiliario / construcción",
    "Logística / transporte",
    "Agricultura / sector primario",
    "ONG / tercer sector",
]

TOP_PARES: list[tuple[str, str]] = [
    ("INT-01", "INT-08"),
    ("INT-02", "INT-17"),
    ("INT-07", "INT-17"),
    ("INT-06", "INT-16"),
    ("INT-05", "INT-17"),
    ("INT-01", "INT-17"),
    ("INT-07", "INT-08"),
    ("INT-14", "INT-01"),
    ("INT-03", "INT-18"),
    ("INT-07", "INT-16"),
]

FIRMAS: dict[str, str] = {
    "INT-01": "Contradicción formal demostrable entre premisas",
    "INT-02": "Dato trivializador ausente + atajo algorítmico",
    "INT-03": "Gap id↔ir + actor invisible con poder",
    "INT-04": "Nichos vacíos + capital biológico en depreciación",
    "INT-05": "Secuencia obligatoria de movimientos + reversibilidad",
    "INT-06": "Poder como objeto + coaliciones no articuladas",
    "INT-07": "Asimetría payoffs cuantificada + tasa de descuento invertida",
    "INT-08": "Vergüenza no nombrada + lealtad invisible",
    "INT-09": "Palabra ausente + acto performativo",
    "INT-10": "Tensión-nudo vs tensión-músculo + arritmia de tempos",
    "INT-11": "Punto de compresión + pendiente gravitacional",
    "INT-12": "Roles arquetípicos + narrativa autoconfirmante",
    "INT-13": "Trampa de escalamiento sectorial + señales débiles",
    "INT-14": "20+ opciones donde el sujeto ve 2",
    "INT-15": "Isomorfismo solución-problema + tristeza anticipatoria",
    "INT-16": "Prototipo con coste, secuencia y fallo seguro",
    "INT-17": "Brecha valores declarados vs vividos + inercia como no-elección",
    "INT-18": "Urgencia inventada + vacío como recurso",
}

INTELIGENCIAS_IDS: list[str] = [f"INT-{i:02d}" for i in range(1, 19)]

# Categorías para validación B1
CUANTITATIVAS: set[str] = {"INT-01", "INT-02", "INT-07"}
HUMANAS: set[str] = {"INT-08", "INT-10", "INT-17", "INT-18"}
