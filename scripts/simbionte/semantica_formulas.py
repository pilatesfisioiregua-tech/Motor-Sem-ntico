"""
Semántica de Fórmulas — Cada fórmula como objeto de razonamiento.

Fecha: 2026-04-13

Cada fórmula tiene 4 capas:
  1. GRAMÁTICA: secuencia de operaciones primitivas (ya en gramatica_formulas.py)
  2. POLOS: eje semántico con dos extremos (qué mide)
  3. PRESUPUESTOS: qué asume sin decirlo (decisiones implícitas)
  4. RAZONAMIENTO: proceso paso a paso con significados (la fórmula como algoritmo de pensamiento)

El LLM no recibe "varianza = 0.034".
Recibe: "la dispersión es baja → todos cerca del centro → no hay extremos → grupo homogéneo".

$0 total (definiciones estáticas)
"""


# ============================================================
# ESTRUCTURA DE CADA FÓRMULA SEMÁNTICA
# ============================================================
#
# "nombre": {
#     "polos": ("polo_bajo", "polo_alto"),
#     "eje": "nombre del eje semántico",
#     "presupuestos": ["qué asume sin decirlo"],
#     "razonamiento": [
#         ("paso", "operación sobre significados", "qué produce"),
#     ],
#     "si_alto": "qué significa cuando el valor es alto",
#     "si_bajo": "qué significa cuando el valor es bajo",
#     "pregunta": "qué pregunta responde esta fórmula",
# }

SEMANTICA = {
    # ============================================================
    # ESTADÍSTICA DESCRIPTIVA
    # ============================================================
    "varianza": {
        "polos": ("concentrado", "disperso"),
        "eje": "dispersión",
        "presupuestos": [
            "El centro es la media aritmética (todos pesan igual)",
            "El cuadrado penaliza extremos desproporcionadamente",
            "La dirección no importa (arriba y abajo pesan igual)",
            "Cada observación pesa igual (no hay privilegiados)",
        ],
        "razonamiento": [
            ("Sumar todos los valores y dividir por n", "Encontrar el punto típico (media)", "SUJETO: el centro de referencia"),
            ("Restar cada valor menos el centro", "Medir cuánto se aleja cada punto", "ADJETIVO: distancia con dirección (+/-)"),
            ("Elevar al cuadrado cada distancia", "Eliminar dirección, amplificar extremos", "TRANSFORMACIÓN: de distancia a magnitud"),
            ("Sumar todas las magnitudes", "Acumular toda la diferencia del grupo", "ACUMULACIÓN: dispersión total"),
            ("Dividir por n", "Normalizar por cantidad", "RESULTADO: dispersión por elemento"),
        ],
        "si_alto": "Los puntos están lejos del centro. Hay extremos. El grupo es heterogéneo. Lo que le pasa al típico NO le pasa a todos.",
        "si_bajo": "Los puntos están cerca del centro. No hay extremos. El grupo es homogéneo. Lo que le pasa al típico le pasa a casi todos.",
        "pregunta": "¿Cuán diferentes son los elementos entre sí?",
    },

    "media": {
        "polos": ("bajo", "alto"),
        "eje": "nivel central",
        "presupuestos": [
            "Todos los valores pesan igual",
            "Los extremos influyen (no es robusta a outliers)",
            "Es el centro democrático, no el más frecuente",
        ],
        "razonamiento": [
            ("Sumar todos los valores", "Acumular en un eje", "ACUMULACIÓN: total del grupo"),
            ("Dividir por n", "Normalizar por cantidad", "RESULTADO: valor típico por elemento"),
        ],
        "si_alto": "El nivel central del grupo está arriba. La mayoría tiene valores altos.",
        "si_bajo": "El nivel central está abajo. La mayoría tiene valores bajos.",
        "pregunta": "¿Dónde está el punto típico del grupo?",
    },

    "correlacion": {
        "polos": ("independientes", "co-dependientes"),
        "eje": "relación lineal",
        "presupuestos": [
            "Solo mide relación LINEAL (puede haber relación no lineal con corr=0)",
            "Correlación ≠ causalidad (pueden moverse juntas por un tercero)",
            "Es simétrica: corr(X,Y) = corr(Y,X) — no dice quién causa a quién",
            "Sensible a outliers (un punto extremo puede crear o destruir correlación)",
        ],
        "razonamiento": [
            ("Para cada X, medir distancia al centro de X", "Cuánto se desvía X de su típico", "ADJETIVO de X: está por encima/debajo"),
            ("Para cada Y, medir distancia al centro de Y", "Cuánto se desvía Y de su típico", "ADJETIVO de Y: está por encima/debajo"),
            ("Multiplicar ambas desviaciones", "Cuando ambos están arriba: producto positivo. Uno arriba y otro abajo: negativo", "COMPOSICIÓN: ¿se desvían en la misma dirección?"),
            ("Sumar todos los productos", "Acumular la concordancia de dirección", "ACUMULACIÓN: co-movimiento total"),
            ("Dividir por n×σx×σy", "Normalizar para que esté entre -1 y +1", "RESULTADO: grado de co-movimiento normalizado"),
        ],
        "si_alto": "Cuando X sube, Y sube (positiva) o baja (negativa). Se mueven JUNTAS. Lo que afecta a una afecta a la otra.",
        "si_bajo": "X e Y se mueven INDEPENDIENTEMENTE. Lo que afecta a una no dice nada sobre la otra.",
        "pregunta": "¿Se mueven juntas estas dos variables?",
    },

    "skewness": {
        "polos": ("cola izquierda (riesgo de caída)", "cola derecha (potencial de subida)"),
        "eje": "asimetría",
        "presupuestos": [
            "El cubo preserva dirección pero amplifica extremos 3x más que la varianza",
            "Asume que la media es el centro relevante",
        ],
        "razonamiento": [
            ("Restar cada valor menos la media", "Distancia con signo", "POSICIÓN relativa al centro"),
            ("Elevar al cubo", "Preservar signo + amplificar extremos brutalmente", "TRANSFORMACIÓN: magnitud direccional extrema"),
            ("Sumar y normalizar", "¿Pesan más los extremos de arriba o los de abajo?", "RESULTADO: hacia dónde se inclina la distribución"),
        ],
        "si_alto": "Hay cola derecha: potencial de resultados extremos positivos. La distribución se estira hacia arriba.",
        "si_bajo": "Hay cola izquierda: riesgo de caídas extremas. La distribución se estira hacia abajo.",
        "pregunta": "¿El riesgo está arriba o abajo?",
    },

    "gini": {
        "polos": ("igualdad perfecta", "un individuo tiene todo"),
        "eje": "desigualdad",
        "presupuestos": [
            "Compara TODOS los pares (no solo rico vs pobre)",
            "No distingue desigualdad arriba vs abajo (Gini=0.4 puede ser pocos ricos o muchos pobres)",
            "Es relativa: no cambia si todos duplican su renta",
        ],
        "razonamiento": [
            ("Ordenar todos los valores de menor a mayor", "Ver la distribución acumulada", "ESTRUCTURA: curva de Lorenz"),
            ("Ponderar cada valor por su posición en la fila", "Los últimos (más ricos) pesan más por su posición", "PONDERACIÓN posicional"),
            ("Normalizar y comparar con igualdad perfecta", "¿Cuán lejos estamos de que todos tengan igual?", "RESULTADO: distancia a la igualdad"),
        ],
        "si_alto": "Pocos tienen mucho, muchos tienen poco. Desigualdad severa. La riqueza se concentra.",
        "si_bajo": "La distribución es equilibrada. Todos tienen cantidades similares.",
        "pregunta": "¿Cuánta desigualdad hay en la distribución?",
    },

    "entropia_shannon": {
        "polos": ("certeza total (un solo tipo)", "incertidumbre máxima (todos los tipos igual)"),
        "eje": "diversidad/incertidumbre",
        "presupuestos": [
            "Usa logaritmo: añadir un tipo nuevo pesa menos cuantos más hay",
            "Todos los tipos son igualmente valiosos (no hay jerarquía)",
            "Mide diversidad de tipos, no de cantidades",
        ],
        "razonamiento": [
            ("Normalizar a proporciones (frecuencias relativas)", "¿Qué fracción es cada tipo?", "DISTRIBUCIÓN de probabilidad"),
            ("Tomar logaritmo de cada proporción", "Comprimir: lo frecuente pesa poco, lo raro pesa mucho", "TRANSFORMACIÓN: sorpresa por tipo"),
            ("Multiplicar proporción × log(proporción)", "Ponderar la sorpresa por cuán frecuente es", "COMPOSICIÓN: sorpresa esperada por tipo"),
            ("Sumar e invertir signo", "Acumular sorpresa total", "RESULTADO: incertidumbre total del sistema"),
        ],
        "si_alto": "Muchos tipos diferentes, ninguno domina. Alta diversidad. Si eliges uno al azar, no sabes cuál será.",
        "si_bajo": "Pocos tipos o uno domina. Baja diversidad. Si eliges al azar, ya sabes qué va a salir.",
        "pregunta": "¿Cuánta sorpresa hay en el sistema?",
    },

    # ============================================================
    # MICROECONOMÍA
    # ============================================================
    "elasticidad_precio": {
        "polos": ("inelástico (insensible)", "elástico (hipersensible)"),
        "eje": "sensibilidad proporcional",
        "presupuestos": [
            "Mide cambios PROPORCIONALES, no absolutos",
            "Asume que la relación es local (cerca del punto actual)",
            "Es caeteris paribus: todo lo demás constante",
        ],
        "razonamiento": [
            ("Medir cambio porcentual en cantidad cuando precio cambia 1%", "¿Cuánto reacciona la demanda?", "SENSIBILIDAD: reacción proporcional"),
            ("Si |ε|<1: inelástico", "La demanda reacciona menos que proporcional", "CONCLUSIÓN: subir precio SUBE ingresos"),
            ("Si |ε|>1: elástico", "La demanda reacciona más que proporcional", "CONCLUSIÓN: subir precio BAJA ingresos"),
            ("Si |ε|=1: unitario", "La demanda reacciona exactamente proporcional", "CONCLUSIÓN: ingresos no cambian"),
        ],
        "si_alto": "Los consumidores son MUY sensibles al precio. Subir precio = perder clientes rápido. Competencia alta o muchos sustitutos.",
        "si_bajo": "Los consumidores son INSENSIBLES al precio. Subir precio = mantener clientes. Necesidad, adicción, o sin sustitutos.",
        "pregunta": "¿Cuánto reacciona la demanda a un cambio de precio?",
    },

    "excedente_consumidor": {
        "polos": ("sin beneficio (paga lo que valora)", "gran beneficio (paga mucho menos de lo que valora)"),
        "eje": "bienestar del consumidor",
        "presupuestos": [
            "Asume que la curva de demanda revela la valoración real",
            "Usa integral: suma continua de valoraciones marginales",
            "Es una aproximación (exacta solo con utilidad cuasilineal)",
        ],
        "razonamiento": [
            ("Para cada unidad, calcular cuánto estaría dispuesto a pagar", "Valoración marginal decreciente", "CURVA de demanda = curva de valoración"),
            ("Integrar todas las valoraciones desde 0 hasta Q*", "Sumar cuánto VALORARÍA pagar en total", "ACUMULACIÓN: valor total percibido"),
            ("Restar precio×cantidad (lo que realmente paga)", "Comparar valoración con gasto real", "COMPARACIÓN: valor - coste"),
            ("La diferencia es el excedente", "Lo que gana por pagar menos de lo que valora", "RESULTADO: beneficio neto del consumidor"),
        ],
        "si_alto": "El consumidor obtiene mucho valor por poco dinero. Está mucho mejor con el intercambio que sin él.",
        "si_bajo": "El consumidor paga casi lo que valora. El intercambio apenas le beneficia. Poder de mercado del vendedor.",
        "pregunta": "¿Cuánto gana el consumidor por participar en este mercado?",
    },

    "indice_lerner": {
        "polos": ("competencia perfecta (cero poder)", "monopolio puro (máximo poder)"),
        "eje": "poder de mercado",
        "presupuestos": [
            "Asume que el precio y el coste marginal son observables",
            "Ignora poder de mercado dinámico (puede tener precio bajo hoy para capturar mañana)",
            "Isomorfo con tasa de crecimiento, output gap y Sharpe (COMPARAR→NORMALIZAR)",
        ],
        "razonamiento": [
            ("Medir precio de venta", "¿Cuánto cobra?", "NIVEL del precio"),
            ("Medir coste marginal", "¿Cuánto le cuesta producir una unidad más?", "NIVEL del coste"),
            ("Restar coste del precio", "¿Cuánto markup hay?", "COMPARACIÓN: distancia precio-coste"),
            ("Dividir por el precio", "Normalizar por el nivel", "RESULTADO: markup como proporción del precio"),
        ],
        "si_alto": "La empresa cobra mucho más de lo que cuesta producir. Tiene poder para fijar precio. Poca competencia.",
        "si_bajo": "La empresa cobra casi lo que cuesta producir. No tiene poder. Mucha competencia le obliga.",
        "pregunta": "¿Cuánto puede la empresa subir el precio sobre su coste?",
    },

    "deadweight_loss": {
        "polos": ("sin pérdida (mercado eficiente)", "pérdida masiva (distorsión severa)"),
        "eje": "ineficiencia social",
        "presupuestos": [
            "Compara con el óptimo de competencia perfecta",
            "Asume que la curva de demanda refleja beneficio social y la de oferta refleja coste social",
            "Ignora externalidades (si las hay, el 'óptimo' puede ser otro)",
        ],
        "razonamiento": [
            ("Comparar precio de mercado con precio competitivo", "¿Cuánto distorsiona el precio?", "DISTORSIÓN en precio"),
            ("Comparar cantidad de mercado con cantidad competitiva", "¿Cuánto se deja de producir?", "DISTORSIÓN en cantidad"),
            ("Multiplicar ambas diferencias × ½ (triángulo)", "Área que nadie captura: ni productor, ni consumidor, ni gobierno", "RESULTADO: bienestar destruido"),
        ],
        "si_alto": "Mucho bienestar se destruye. Transacciones que beneficiarían a ambas partes no ocurren. La economía funciona mal.",
        "si_bajo": "Poco bienestar perdido. El mercado funciona cerca del óptimo. La distorsión es pequeña.",
        "pregunta": "¿Cuánto bienestar se destruye por la distorsión del mercado?",
    },

    # ============================================================
    # MACROECONOMÍA
    # ============================================================
    "output_gap": {
        "polos": ("recesión (bajo potencial)", "sobrecalentamiento (sobre potencial)"),
        "eje": "presión cíclica",
        "presupuestos": [
            "Asume que el PIB potencial es observable (no lo es — se estima)",
            "Isomorfo con Lerner, tasa de crecimiento y Sharpe (COMPARAR→NORMALIZAR)",
            "Simétrico: desviaciones arriba y abajo se tratan igual",
        ],
        "razonamiento": [
            ("Medir PIB real actual", "¿Dónde estamos?", "NIVEL actual"),
            ("Estimar PIB potencial", "¿Dónde deberíamos estar?", "REFERENCIA: capacidad de la economía"),
            ("Restar real menos potencial", "¿Estamos por encima o por debajo?", "COMPARACIÓN: distancia al potencial"),
            ("Dividir por potencial", "Normalizar", "RESULTADO: desviación proporcional"),
        ],
        "si_alto": "La economía produce MÁS de lo que puede sostener. Presión inflacionaria. Mercado laboral tensionado. Necesita enfriarse.",
        "si_bajo": "La economía produce MENOS de lo que puede. Capacidad ociosa. Desempleo. Necesita estímulo.",
        "pregunta": "¿La economía está por encima o por debajo de su capacidad?",
    },

    "regla_taylor": {
        "polos": ("tipos bajos (estímulo)", "tipos altos (restricción)"),
        "eje": "postura monetaria",
        "presupuestos": [
            "Asume que el banco central puede y debe seguir una regla",
            "Asume pesos iguales (0.5) a inflación y output gap — juicio de valor",
            "Requiere conocer la tasa natural (r*) y el PIB potencial — ambos no observables",
        ],
        "razonamiento": [
            ("Medir inflación actual vs objetivo", "¿Cuánto se desvía la inflación?", "DESVIACIÓN inflacionaria"),
            ("Medir output gap", "¿Está la economía caliente o fría?", "DESVIACIÓN de actividad"),
            ("Ponderar ambas desviaciones por 0.5", "Dar peso igual a ambas preocupaciones", "PONDERACIÓN: estabilidad de precios vs empleo"),
            ("Sumar con tasa natural + inflación actual", "Construir la prescripción", "RESULTADO: tipo de interés que debería fijar el banco central"),
        ],
        "si_alto": "El banco central debería restringir. Inflación alta y/o economía sobrecalentada.",
        "si_bajo": "El banco central debería estimular. Inflación baja y/o economía fría.",
        "pregunta": "¿A qué tipo de interés debería estar el banco central?",
    },

    "multiplicador_fiscal": {
        "polos": ("ineficaz (multiplicador < 1)", "amplificador (multiplicador > 1)"),
        "eje": "potencia fiscal",
        "presupuestos": [
            "Asume propensión marginal a consumir constante",
            "Ignora efectos de crowding out (el gasto público desplaza inversión privada)",
            "Asume economía cerrada (en economía abierta, parte se va en importaciones)",
            "No distingue tipo de gasto (infraestructura vs transferencias)",
        ],
        "razonamiento": [
            ("El gobierno gasta 1€ adicional", "Un agente recibe 1€ más", "IMPULSO inicial"),
            ("Ese agente consume c×1€ (c = propensión a consumir)", "Parte del € se gasta, parte se ahorra", "PRIMERA RONDA: el € circula parcialmente"),
            ("El siguiente agente recibe c€ y consume c²€", "El € sigue circulando, cada vez más pequeño", "RONDAS SUCESIVAS: serie geométrica decreciente"),
            ("Sumar todas las rondas: 1/(1-c)", "Total acumulado de actividad generada", "RESULTADO: cuántos € de PIB genera cada € de gasto"),
        ],
        "si_alto": "Cada euro de gasto público genera más de un euro de PIB. La economía amplifica el impulso. Política fiscal potente.",
        "si_bajo": "Cada euro genera menos de un euro. El dinero se filtra (ahorro, impuestos, importaciones). Política fiscal débil.",
        "pregunta": "¿Cuánto PIB genera cada euro de gasto público?",
    },

    "curva_phillips": {
        "polos": ("deflación/desempleo alto", "inflación/pleno empleo"),
        "eje": "trade-off inflación-empleo",
        "presupuestos": [
            "Asume relación estable entre inflación y desempleo — puede no serlo (estanflación)",
            "Isomorfo con CAPM (COMPARAR→ESCALAR→ACUMULAR)",
            "Versión moderna incluye expectativas — si la gente espera inflación, la relación cambia",
        ],
        "razonamiento": [
            ("Medir output gap (o desempleo vs NAIRU)", "¿Cuánta presión hay en el mercado laboral?", "PRESIÓN de demanda"),
            ("Escalar por sensibilidad (κ)", "¿Cuánta inflación genera cada punto de gap?", "TRANSMISIÓN: de actividad a precios"),
            ("Sumar expectativas de inflación", "Lo que la gente ESPERA que pase se autocumple", "COMPONENTE inercial"),
            ("Resultado: inflación", "Inflación = expectativas + presión de demanda", "RESULTADO: por qué suben los precios"),
        ],
        "si_alto": "Economía caliente: mucha demanda, poco desempleo, precios subiendo. Típico final de expansión.",
        "si_bajo": "Economía fría: poca demanda, mucho desempleo, precios estables o cayendo. Típico recesión.",
        "pregunta": "¿Cuánta inflación genera la presión de la demanda?",
    },

    # ============================================================
    # FINANZAS
    # ============================================================
    "capm": {
        "polos": ("retorno bajo (activo seguro)", "retorno alto (activo arriesgado)"),
        "eje": "retorno justo por riesgo",
        "presupuestos": [
            "Solo el riesgo SISTEMÁTICO (de mercado) se compensa — el específico se diversifica",
            "Asume mercados eficientes y agentes racionales",
            "Isomorfo con Phillips (COMPARAR→ESCALAR→ACUMULAR)",
            "Beta mide sensibilidad al mercado, no riesgo total",
        ],
        "razonamiento": [
            ("Medir retorno del mercado menos tasa libre de riesgo", "¿Cuánto paga el mercado por arriesgar?", "PRIMA de mercado"),
            ("Multiplicar por beta del activo", "¿Cuánto de ese riesgo tiene este activo?", "ESCALAR: exposición individual al riesgo"),
            ("Sumar tasa libre de riesgo", "Añadir la base de retorno sin riesgo", "RESULTADO: retorno que DEBERÍA tener el activo"),
        ],
        "si_alto": "El activo debería rendir mucho porque tiene mucho riesgo sistemático. Si rinde menos, está sobrevalorado.",
        "si_bajo": "El activo debería rendir poco porque tiene poco riesgo. Si rinde más, es una ganga.",
        "pregunta": "¿Cuánto debería rendir este activo dado su riesgo?",
    },

    "sharpe": {
        "polos": ("mal compensado (poco retorno por mucho riesgo)", "bien compensado (mucho retorno por poco riesgo)"),
        "eje": "eficiencia riesgo-retorno",
        "presupuestos": [
            "Usa desviación estándar como medida de riesgo (asume normalidad)",
            "Isomorfo con Lerner, crecimiento, output gap (COMPARAR→NORMALIZAR)",
            "No distingue volatilidad alcista de bajista (ambas son 'riesgo')",
        ],
        "razonamiento": [
            ("Medir retorno del activo menos tasa libre de riesgo", "¿Cuánto exceso de retorno hay?", "PREMIO por arriesgar"),
            ("Dividir por volatilidad (desviación estándar)", "Normalizar por cuánto riesgo asumes", "RESULTADO: premio por unidad de riesgo"),
        ],
        "si_alto": "Estás bien pagado por el riesgo que tomas. Inversión eficiente.",
        "si_bajo": "Estás mal pagado. Podrías obtener el mismo retorno con menos riesgo (o más retorno con el mismo riesgo).",
        "pregunta": "¿Estás bien compensado por el riesgo que asumes?",
    },

    "valor_presente_neto": {
        "polos": ("destruye valor (VPN < 0)", "crea valor (VPN > 0)"),
        "eje": "creación de valor",
        "presupuestos": [
            "La tasa de descuento refleja el coste de oportunidad — pero ¿cuál es?",
            "Asume que los flujos futuros son conocidos (en realidad son estimaciones)",
            "Un € hoy vale más que un € mañana — ¿cuánto más? Depende de r",
        ],
        "razonamiento": [
            ("Para cada flujo futuro, dividir por (1+r)^t", "¿Cuánto vale hoy lo que recibirás en t períodos?", "DESCUENTO: el futuro vale menos que el presente"),
            ("Sumar todos los flujos descontados", "¿Cuánto vale hoy la suma de todos los cobros y pagos futuros?", "ACUMULACIÓN: valor presente total"),
            ("Si es positivo, la inversión crea valor. Si negativo, lo destruye.", "Comparar con cero", "RESULTADO: ¿vale la pena invertir?"),
        ],
        "si_alto": "La inversión genera más de lo que cuesta financiarla. Crea valor. Hazla.",
        "si_bajo": "La inversión cuesta más de lo que genera. Destruye valor. No la hagas.",
        "pregunta": "¿Cuánto valor crea o destruye esta inversión?",
    },

    # ============================================================
    # ECONOMETRÍA
    # ============================================================
    "ols": {
        "polos": ("sin efecto (β = 0)", "efecto fuerte (β grande)"),
        "eje": "efecto estimado",
        "presupuestos": [
            "Asume linealidad (Y = a + bX + error)",
            "Asume que los errores son independientes de X (exogeneidad)",
            "Asume que no hay variables omitidas correlacionadas con X",
            "Isomorfo con IV/2SLS (COMPONER→INVERTIR→COMPONER) — misma gramática, diferente pureza",
        ],
        "razonamiento": [
            ("Multiplicar X'X (varianza de X)", "¿Cuánta variación hay en la variable explicativa?", "BASE: información disponible"),
            ("Invertir X'X", "Preparar para resolver el sistema", "INVERSIÓN: deshacer la varianza"),
            ("Multiplicar por X'y (covarianza de X e Y)", "¿Cuánto se mueven juntas X e Y?", "COMPOSICIÓN: relación cruda"),
            ("Resultado: β = cuánto cambia Y por unidad de cambio en X", "El efecto estimado", "RESULTADO: si X sube 1, Y sube β"),
        ],
        "si_alto": "X tiene un efecto fuerte sobre Y. Un cambio pequeño en X produce un cambio grande en Y.",
        "si_bajo": "X tiene poco efecto sobre Y. Cambiar X apenas mueve Y.",
        "pregunta": "¿Cuánto cambia Y cuando X cambia en una unidad?",
    },

    "did": {
        "polos": ("sin efecto del tratamiento", "efecto causal fuerte"),
        "eje": "efecto causal",
        "presupuestos": [
            "Asume TENDENCIAS PARALELAS: sin tratamiento, tratados y control habrían evolucionado igual",
            "Este supuesto NO es testeable — es una apuesta de fe",
            "Solo 3 operaciones COMPARAR — es la más limpia de las técnicas causales",
        ],
        "razonamiento": [
            ("Medir cambio antes→después en el grupo tratado", "¿Cuánto cambió el grupo que recibió el tratamiento?", "PRIMERA COMPARACIÓN: cambio bruto"),
            ("Medir cambio antes→después en el grupo control", "¿Cuánto cambió el grupo que NO recibió el tratamiento?", "SEGUNDA COMPARACIÓN: contrafactual"),
            ("Restar: cambio_tratado - cambio_control", "Eliminar lo que habría pasado de todos modos", "TERCERA COMPARACIÓN: efecto neto = efecto causal"),
        ],
        "si_alto": "El tratamiento tuvo un efecto grande. La política/intervención funcionó.",
        "si_bajo": "El tratamiento no tuvo efecto o fue pequeño. La política no cambió nada.",
        "pregunta": "¿Cuál es el efecto CAUSAL del tratamiento, descontando lo que habría pasado sin él?",
    },

    "r_cuadrado": {
        "polos": ("no explica nada (R²=0)", "explica todo (R²=1)"),
        "eje": "poder explicativo",
        "presupuestos": [
            "No dice si el modelo es CORRECTO, solo si ajusta bien",
            "R² alto con modelo incorrecto = sobreajuste",
            "Nunca baja al añadir variables (por eso existe R² ajustado)",
        ],
        "razonamiento": [
            ("Calcular variación total de Y (cuánto varía Y en total)", "¿Cuánta variación hay que explicar?", "DENOMINADOR: variación total"),
            ("Calcular variación residual (lo que el modelo NO explica)", "¿Cuánto queda sin explicar?", "NUMERADOR: lo que falla"),
            ("R² = 1 - (residual/total)", "Proporción de variación explicada", "RESULTADO: fracción del mundo que entiendes"),
        ],
        "si_alto": "El modelo explica la mayor parte de la variación. Entiendes bien qué mueve Y.",
        "si_bajo": "El modelo explica poco. Hay fuerzas que mueven Y que no estás capturando.",
        "pregunta": "¿Cuánta de la variación de Y captura mi modelo?",
    },

    # ============================================================
    # OPTIMIZACIÓN
    # ============================================================
    "bellman": {
        "polos": ("estado sin valor (callejón sin salida)", "estado muy valioso (posición privilegiada)"),
        "eje": "valor de una situación",
        "presupuestos": [
            "Asume que puedes evaluar el futuro (conoces la función de transición)",
            "Descuenta el futuro por β — el presente vale más",
            "Principio de optimalidad: si la decisión global es óptima, cada subdecisión también lo es",
        ],
        "razonamiento": [
            ("Para cada acción posible, calcular recompensa inmediata", "¿Cuánto gano AHORA?", "VALOR PRESENTE"),
            ("Para cada acción, calcular el valor del estado al que llego × descuento", "¿Cuánto vale el FUTURO al que me lleva esta acción?", "VALOR FUTURO descontado"),
            ("Sumar presente + futuro", "¿Cuánto vale cada acción en total?", "VALOR TOTAL de cada opción"),
            ("Elegir la acción con mayor valor total", "¿Cuál es la mejor opción?", "RESULTADO: decisión óptima + valor del estado"),
        ],
        "si_alto": "Estás en una buena posición. Tienes opciones valiosas. El futuro desde aquí es prometedor.",
        "si_bajo": "Estás en una mala posición. Tus opciones son pobres. Difícil mejorar desde aquí.",
        "pregunta": "¿Cuánto vale estar en esta situación, considerando todas las decisiones futuras óptimas?",
    },

    # ============================================================
    # CONDUCTUAL
    # ============================================================
    "prospect_value": {
        "polos": ("pérdida percibida (dolor amplificado)", "ganancia percibida (placer atenuado)"),
        "eje": "valor percibido asimétrico",
        "presupuestos": [
            "Las pérdidas pesan ~2.5x más que las ganancias equivalentes",
            "Sensibilidad decreciente: la diferencia entre 100→200 se siente más que 1000→1100",
            "El punto de referencia (el 'cero') no es objetivo — depende de expectativas",
        ],
        "razonamiento": [
            ("¿Es ganancia o pérdida? (respecto al punto de referencia)", "Clasificar por signo", "CONDICIÓN: ¿estás mejor o peor que tu referencia?"),
            ("Si ganancia: aplicar x^0.88 (concavidad)", "Sensibilidad decreciente: más no impresiona tanto", "TRANSFORMACIÓN: rendimientos decrecientes de alegría"),
            ("Si pérdida: aplicar -2.25×|x|^0.88 (convexidad + amplificación)", "El dolor es convexo Y amplificado", "TRANSFORMACIÓN: el dolor crece más que la alegría"),
        ],
        "si_alto": "Ganancia: placer moderado. Cuanto más ganas, menos alegría marginal.",
        "si_bajo": "Pérdida: dolor intenso y desproporcionado. Perder 100€ duele 2.5x más que alegra ganar 100€.",
        "pregunta": "¿Cuánto vale esta situación PERCIBIDA, no objetivamente?",
    },

    # ============================================================
    # RELACIONES MACRO
    # ============================================================
    "persistencia": {
        "polos": ("transitorio (se disipa rápido)", "estructural (permanece)"),
        "eje": "duración del shock",
        "presupuestos": [
            "Mide autocorrelación de primer orden (AR(1))",
            "Asume que la estructura no cambia en el tiempo",
        ],
        "razonamiento": [
            ("Medir correlación entre valor actual y valor rezagado", "¿Cuánto del pasado permanece en el presente?", "MEMORIA: el ayer explica el hoy"),
            ("Si ρ → 1: cada shock se acumula permanentemente", "Lo que pasa no se deshace", "RESULTADO: shock permanente"),
            ("Si ρ → 0: cada shock desaparece en un período", "Mañana es independiente de hoy", "RESULTADO: shock transitorio"),
        ],
        "si_alto": "Los shocks son ESTRUCTURALES. Lo que cambia, permanece. Requiere intervención activa para revertir.",
        "si_bajo": "Los shocks son TRANSITORIOS. Se disipan solos. Mejor no intervenir y esperar.",
        "pregunta": "¿Este cambio es permanente o se va solo?",
    },

    "gap": {
        "polos": ("bajo potencial (capacidad ociosa)", "sobre potencial (sobrecalentamiento)"),
        "eje": "posición relativa a la tendencia",
        "presupuestos": [
            "Asume que la tendencia es observable o estimable",
            "La tendencia ≠ el óptimo (puede estar por encima de lo sostenible)",
        ],
        "razonamiento": [
            ("Medir valor actual", "¿Dónde estoy?", "POSICIÓN actual"),
            ("Estimar tendencia (media, filtro HP, regresión)", "¿Dónde debería estar?", "REFERENCIA"),
            ("Restar y normalizar", "¿Cuánto me desvío de lo normal?", "RESULTADO: distancia al potencial"),
        ],
        "si_alto": "Estás POR ENCIMA de la tendencia. Puede ser bueno (boom) o peligroso (burbuja). No es sostenible indefinidamente.",
        "si_bajo": "Estás POR DEBAJO de la tendencia. Hay capacidad sin usar. Oportunidad de crecer o señal de problema.",
        "pregunta": "¿Estoy por encima o por debajo de lo normal?",
    },

    "elasticidad_general": {
        "polos": ("insensible (inelástico)", "hipersensible (elástico)"),
        "eje": "sensibilidad proporcional",
        "presupuestos": [
            "Mide cambios RELATIVOS, no absolutos",
            "Es local (cerca del punto actual)",
            "Isomorfa con cualquier otra elasticidad (DERIVAR→NORMALIZAR)",
        ],
        "razonamiento": [
            ("Derivar Y respecto a X (¿cuánto cambia Y por unidad de X?)", "Sensibilidad absoluta", "DERIVADA: velocidad de cambio"),
            ("Normalizar por niveles de X e Y", "Pasar de absoluto a proporcional", "RESULTADO: si X sube 1%, Y sube ε%"),
        ],
        "si_alto": "Y reacciona MUCHO a cambios en X. Pequeños movimientos en X producen grandes movimientos en Y.",
        "si_bajo": "Y apenas reacciona a X. Puedes mover X mucho y Y casi no cambia.",
        "pregunta": "¿Cuánto reacciona Y proporcionalmente a un cambio proporcional en X?",
    },
}

# Bloque 2: fórmulas adicionales
SEMANTICA_2 = {
    # ============================================================
    # ESTADÍSTICA DESCRIPTIVA (restantes)
    # ============================================================
    "desviacion_estandar": {
        "polos": ("concentrado", "disperso"), "eje": "dispersión en unidades originales",
        "presupuestos": ["Mismos que varianza pero en escala original (raíz cuadrada devuelve al eje)", "Más interpretable que varianza pero menos tratable matemáticamente"],
        "razonamiento": [("Calcular varianza", "dispersión al cuadrado", "magnitud cuadrada"), ("Raíz cuadrada", "volver al eje original", "RESULTADO: dispersión en las mismas unidades que los datos")],
        "si_alto": "Los datos varían mucho alrededor del centro.", "si_bajo": "Los datos están agrupados cerca del centro.",
        "pregunta": "¿Cuánto varían los datos en sus propias unidades?",
    },
    "coeficiente_variacion": {
        "polos": ("predecible", "impredecible"), "eje": "dispersión relativa",
        "presupuestos": ["Normaliza por la media — comparable entre variables con diferentes escalas", "Pierde sentido si la media es cercana a cero"],
        "razonamiento": [("Calcular desviación estándar", "dispersión absoluta", "cuánto varían"), ("Dividir por la media", "relativizar", "RESULTADO: cuánto varían RESPECTO a su nivel")],
        "si_alto": "Variable impredecible — su variación es grande respecto a su nivel.", "si_bajo": "Variable predecible — su variación es pequeña respecto a su nivel.",
        "pregunta": "¿Cuán impredecible es esta variable respecto a su nivel?",
    },
    "kurtosis": {
        "polos": ("colas ligeras (sin extremos)", "colas pesadas (extremos probables)"), "eje": "riesgo de eventos extremos",
        "presupuestos": ["Cuarta potencia amplifica extremos brutalmente", "Kurtosis=3 es 'normal' (mesokúrtica)", "No dice cuán grande será el extremo, solo cuán probable"],
        "razonamiento": [("Elevar desviaciones a la cuarta potencia", "Amplificar extremos exponencialmente", "Detectar colas"), ("Normalizar", "Comparar con distribución normal", "RESULTADO: cuán probable es un cisne negro")],
        "si_alto": "Eventos extremos son más probables de lo que parece. Cuidado con los cisnes negros.", "si_bajo": "Eventos extremos son raros. La distribución es bien comportada.",
        "pregunta": "¿Cuán probables son los eventos extremos?",
    },
    "percentil": {
        "polos": ("cola inferior", "cola superior"), "eje": "posición en la distribución",
        "presupuestos": ["No asume forma de distribución (no paramétrico)", "Ordena todos los datos — sensible a la muestra"],
        "razonamiento": [("Ordenar todos los valores", "Crear ranking", "posición relativa"), ("Seleccionar el valor en la posición k%", "Encontrar umbral", "RESULTADO: qué valor deja k% debajo")],
        "si_alto": "Este valor está en la cola superior — mejor que la mayoría.", "si_bajo": "Este valor está en la cola inferior — peor que la mayoría.",
        "pregunta": "¿Dónde está este valor en la distribución?",
    },
    "mediana": {
        "polos": ("bajo", "alto"), "eje": "centro robusto",
        "presupuestos": ["Inmune a outliers (a diferencia de la media)", "Ignora magnitud — solo mira posición"],
        "razonamiento": [("Ordenar valores", "Ranking", "secuencia"), ("Tomar el del medio", "Centro posicional", "RESULTADO: valor típico que ignora extremos")],
        "si_alto": "El centro real del grupo está arriba.", "si_bajo": "El centro real está abajo.",
        "pregunta": "¿Cuál es el valor central ignorando extremos?",
    },

    # ============================================================
    # MICRO: Consumidor (restantes)
    # ============================================================
    "utilidad_marginal": {
        "polos": ("saciado (utilidad marginal ~0)", "hambriento (utilidad marginal alta)"), "eje": "satisfacción incremental",
        "presupuestos": ["Asume utilidad diferenciable", "Decreciente por convexidad de preferencias"],
        "razonamiento": [("Derivar utilidad respecto a la cantidad", "¿Cuánto más feliz te hace una unidad más?", "RESULTADO: satisfacción por unidad adicional")],
        "si_alto": "Cada unidad adicional aporta mucha satisfacción. Quieres más.", "si_bajo": "Ya tienes suficiente. Una unidad más apenas importa.",
        "pregunta": "¿Cuánta satisfacción adicional da una unidad más?",
    },
    "tasa_marginal_sustitucion": {
        "polos": ("complementarios (no sustituyes)", "sustitutos (intercambias fácilmente)"), "eje": "sustituibilidad",
        "presupuestos": ["Mide sobre curva de indiferencia (utilidad constante)", "Es local — puede cambiar en otros puntos"],
        "razonamiento": [("Medir utilidad marginal de X y de Y", "¿Cuánto valoras cada uno?", "Valoraciones"), ("Dividir UMx/UMy", "Ratio de valoraciones", "RESULTADO: cuántas unidades de Y sacrificas por 1 más de X")],
        "si_alto": "X vale mucho más que Y para ti. Sacrificas mucho Y por poco X.", "si_bajo": "X y Y valen similar. No sacrificas mucho de uno por el otro.",
        "pregunta": "¿Cuánto de Y estás dispuesto a dar por una unidad más de X?",
    },
    "excedente_productor": {
        "polos": ("sin margen", "alto margen"), "eje": "beneficio del productor",
        "presupuestos": ["Simétrico al excedente del consumidor", "Área entre precio y curva de oferta"],
        "razonamiento": [("Calcular precio de mercado × cantidad", "Ingreso total", "Lo que cobra"), ("Restar coste variable total (integral de CMg)", "Lo que cuesta", "COMPARACIÓN"), ("La diferencia es el excedente", "Beneficio variable", "RESULTADO: cuánto gana por encima de sus costes")],
        "si_alto": "El productor cobra mucho más de lo que le cuesta. Buen negocio.", "si_bajo": "El productor cobra casi lo que le cuesta. Negocio marginal.",
        "pregunta": "¿Cuánto gana el productor por participar en este mercado?",
    },
    "coste_marginal": {
        "polos": ("barato producir más", "caro producir más"), "eje": "coste incremental",
        "presupuestos": ["Isomorfo con utilidad marginal (DERIVAR)", "Creciente en el corto plazo (rendimientos decrecientes)"],
        "razonamiento": [("Derivar coste total respecto a cantidad", "¿Cuánto más cuesta una unidad más?", "RESULTADO: coste de la siguiente unidad")],
        "si_alto": "Producir más es cada vez más caro. Capacidad saturada.", "si_bajo": "Producir más es barato. Hay capacidad ociosa.",
        "pregunta": "¿Cuánto cuesta producir una unidad más?",
    },
    "hhi": {
        "polos": ("fragmentado (muchos pequeños)", "concentrado (pocos grandes)"), "eje": "concentración de mercado",
        "presupuestos": ["Solo mira cuotas, no barreras ni comportamiento", "Cuadrado amplifica a los grandes"],
        "razonamiento": [("Calcular cuota de mercado de cada empresa", "¿Qué % tiene cada una?", "Participaciones"), ("Elevar al cuadrado cada cuota", "Amplificar a los grandes, minimizar a los pequeños", "PONDERACIÓN"), ("Sumar", "Índice de concentración", "RESULTADO: cuán dominado está el mercado")],
        "si_alto": "Pocas empresas dominan. Riesgo de colusión y precios altos.", "si_bajo": "Muchas empresas pequeñas. Competencia intensa.",
        "pregunta": "¿Cuántas empresas dominan este mercado?",
    },
    "equilibrio_nash": {
        "polos": ("inestable (incentivo a desviarse)", "estable (nadie mejora cambiando)"), "eje": "estabilidad estratégica",
        "presupuestos": ["Cada jugador es racional y conoce las estrategias del otro", "Puede haber múltiples equilibrios", "No necesariamente es el mejor resultado posible"],
        "razonamiento": [("Para cada jugador, calcular mejor respuesta dado lo que hacen los demás", "¿Qué harías si los demás no cambian?", "Mejor respuesta"), ("Encontrar punto donde todas las mejores respuestas son consistentes", "Nadie quiere cambiar", "RESULTADO: equilibrio — estado estable del conflicto")],
        "si_alto": "El equilibrio es fuerte: desviarse cuesta mucho. Situación difícil de cambiar.", "si_bajo": "El equilibrio es débil: un pequeño cambio puede romperlo.",
        "pregunta": "¿Hay una situación donde nadie quiere cambiar su estrategia?",
    },
    "valor_shapley": {
        "polos": ("no contribuye", "contribuye mucho"), "eje": "contribución justa",
        "presupuestos": ["Mide contribución marginal MEDIA sobre todas las coaliciones posibles", "Es el único valor que cumple eficiencia+simetría+nulidad+aditividad"],
        "razonamiento": [("Para cada coalición posible, medir valor con y sin el jugador", "¿Cuánto añade?", "Contribución marginal"), ("Promediar sobre todas las coaliciones ponderado por combinatoria", "Promediar el orden de llegada", "RESULTADO: contribución justa")],
        "si_alto": "Este jugador aporta mucho. Sin él, el grupo vale significativamente menos.", "si_bajo": "Este jugador es prescindible. El grupo funciona similar sin él.",
        "pregunta": "¿Cuánto contribuye justamente cada jugador al resultado del grupo?",
    },

    # ============================================================
    # MACRO (restantes)
    # ============================================================
    "solow_steady_state": {
        "polos": ("subdesarrollado (lejos del estado estacionario)", "desarrollado (en estado estacionario)"), "eje": "posición de largo plazo",
        "presupuestos": ["Rendimientos decrecientes del capital", "Ahorro exógeno y constante", "Sin progreso técnico en versión básica"],
        "razonamiento": [("Calcular inversión: s×f(k)", "¿Cuánto capital nuevo se crea?", "INVERSIÓN"), ("Calcular depreciación: (n+δ)×k", "¿Cuánto capital se destruye?", "DEPRECIACIÓN"), ("Encontrar k* donde inversión = depreciación", "Equilibrio de largo plazo", "RESULTADO: nivel de capital sostenible")],
        "si_alto": "Alto capital por trabajador = economía rica. Pero crecimiento se frena (rendimientos decrecientes).", "si_bajo": "Bajo capital = economía pobre pero con potencial de crecimiento rápido (convergencia).",
        "pregunta": "¿Cuál es el nivel de riqueza de largo plazo de esta economía?",
    },
    "residuo_solow": {
        "polos": ("sin innovación (todo se explica por capital+trabajo)", "alta innovación (la productividad crece sola)"), "eje": "progreso tecnológico",
        "presupuestos": ["'La medida de nuestra ignorancia' (Solow)", "Recoge TODO lo que no es capital ni trabajo (instituciones, educación, tecnología, errores de medición)"],
        "razonamiento": [("Medir crecimiento del PIB", "¿Cuánto creció?", "TOTAL"), ("Restar contribución de capital (α×ΔK/K) y trabajo ((1-α)×ΔL/L)", "¿Cuánto explican los factores?", "FACTORES"), ("Lo que sobra es el residuo", "Lo que no se explica", "RESULTADO: productividad total de los factores")],
        "si_alto": "La economía crece por innovación, no por acumular más. Crecimiento sano y sostenible.", "si_bajo": "El crecimiento viene solo de más capital o más trabajadores. Insostenible sin innovación.",
        "pregunta": "¿Cuánto del crecimiento viene de la innovación vs acumulación bruta?",
    },
    "ecuacion_fisher": {
        "polos": ("tipo real negativo (la inflación se come los intereses)", "tipo real positivo (los intereses superan la inflación)"), "eje": "coste real del dinero",
        "presupuestos": ["Solo una resta — la fórmula más simple y más importante de la macro", "Isomorfa con Modigliani-Miller, Bertrand, dominancia estocástica (COMPARAR)"],
        "razonamiento": [("Tomar tipo de interés nominal", "¿Cuánto te paga el banco?", "NOMINAL"), ("Restar inflación esperada", "¿Cuánto te quita la inflación?", "INFLACIÓN"), ("La diferencia es el tipo real", "¿Cuánto ganas de verdad?", "RESULTADO: el precio real del dinero")],
        "si_alto": "El dinero tiene valor real positivo. Ahorrar compensa. Política monetaria restrictiva.", "si_bajo": "La inflación se come los intereses. Ahorrar es perder. Incentivo a gastar/invertir/especular.",
        "pregunta": "¿Cuál es el coste real de pedir prestado (o el retorno real de ahorrar)?",
    },
    "tasa_crecimiento": {
        "polos": ("contracción", "expansión"), "eje": "velocidad de la economía",
        "presupuestos": ["Isomorfa con Lerner, output gap, Sharpe (COMPARAR→NORMALIZAR)", "Solo mide velocidad, no dirección ni sostenibilidad"],
        "razonamiento": [("Restar valor actual menos anterior", "¿Cuánto cambió?", "CAMBIO absoluto"), ("Dividir por valor anterior", "Normalizar por el nivel", "RESULTADO: cambio proporcional")],
        "si_alto": "La economía crece rápido. Puede ser sano o burbuja — depende de qué crece.", "si_bajo": "La economía se contrae. Puede ser recesión o ajuste necesario.",
        "pregunta": "¿A qué velocidad crece o decrece?",
    },
    "inflacion": {
        "polos": ("deflación (precios caen)", "inflación alta (precios suben rápido)"), "eje": "velocidad de cambio de precios",
        "presupuestos": ["Es una tasa de cambio del nivel de precios", "Inflación moderada (~2%) es objetivo de la mayoría de bancos centrales"],
        "razonamiento": [("Medir nivel de precios hoy vs ayer", "¿Cuánto subieron?", "CAMBIO"), ("Normalizar", "Cambio proporcional", "RESULTADO: velocidad de subida de precios")],
        "si_alto": "Los precios suben rápido. Poder adquisitivo se erosiona. Incertidumbre.", "si_bajo": "Los precios bajan (deflación). Incentivo a no gastar (esperar precios más bajos). Trampa deflacionaria.",
        "pregunta": "¿A qué velocidad cambian los precios?",
    },
    "deuda_pib": {
        "polos": ("solvente (baja deuda)", "vulnerable (alta deuda)"), "eje": "sostenibilidad fiscal",
        "presupuestos": ["No hay umbral mágico (60%, 90%... depende del país)", "Lo que importa es r-g: si tipos > crecimiento, la deuda explota"],
        "razonamiento": [("Medir deuda total", "¿Cuánto debe?", "OBLIGACIÓN"), ("Dividir por PIB", "¿Cuánto produce?", "CAPACIDAD de pago"), ("El ratio dice cuántos años de producción se necesitan para pagar", "Sostenibilidad", "RESULTADO: carga fiscal relativa")],
        "si_alto": "Deuda alta relativa al PIB. Vulnerable a shocks de tipos de interés. Margen fiscal limitado.", "si_bajo": "Deuda manejable. Margen para estímulo fiscal si es necesario.",
        "pregunta": "¿Cuánta deuda tiene el gobierno relativa a lo que produce la economía?",
    },
    "dyn_deuda": {
        "polos": ("deuda converge (sostenible)", "deuda diverge (insostenible)"), "eje": "dinámica fiscal",
        "presupuestos": ["r-g es el factor clave: si tipo de interés > crecimiento, la deuda crece sola", "El superávit primario es lo que el gobierno controla"],
        "razonamiento": [("Comparar tipo de interés (r) con crecimiento (g)", "¿La deuda crece más rápido que la economía?", "DINÁMICA automática"), ("Multiplicar (r-g) por ratio deuda actual", "¿Cuánto sube la deuda por inercia?", "EFECTO bola de nieve"), ("Restar superávit primario", "¿Cuánto compensa el gobierno con impuestos-gasto?", "RESULTADO: si la deuda sube o baja")],
        "si_alto": "r>g y déficit: la deuda explota. Espiral fiscal. Crisis inminente sin ajuste.", "si_bajo": "g>r o superávit: la deuda se reduce sola. Sostenible.",
        "pregunta": "¿La deuda está en trayectoria sostenible o explosiva?",
    },

    # ============================================================
    # FINANZAS (restantes)
    # ============================================================
    "beta_capm": {
        "polos": ("defensivo (β<1)", "agresivo (β>1)"), "eje": "sensibilidad al mercado",
        "presupuestos": ["Solo mide riesgo SISTEMÁTICO", "Asume relación lineal y estable con el mercado"],
        "razonamiento": [("Calcular covarianza del activo con el mercado", "¿Se mueven juntos?", "CO-MOVIMIENTO"), ("Dividir por varianza del mercado", "Normalizar", "RESULTADO: cuánto se mueve el activo por cada 1% del mercado")],
        "si_alto": "Activo agresivo: amplifica los movimientos del mercado. Sube más cuando todo sube, cae más cuando todo cae.", "si_bajo": "Activo defensivo: amortigua los movimientos del mercado.",
        "pregunta": "¿Cuánto amplifica o amortigua este activo los movimientos del mercado?",
    },
    "var_parametrico": {
        "polos": ("riesgo bajo", "riesgo alto"), "eje": "pérdida máxima probable",
        "presupuestos": ["Asume distribución normal (falla en colas pesadas)", "No dice cuánto pierdes en el peor caso, solo el umbral"],
        "razonamiento": [("Tomar media de retornos", "Retorno esperado", "CENTRO"), ("Restar z_α × desviación", "Bajar z desviaciones estándar", "UMBRAL"), ("RESULTADO: con X% de confianza, no perderás más que esto", "Pérdida máxima probable", "RESULTADO")],
        "si_alto": "Puedes perder mucho. Posición arriesgada.", "si_bajo": "Pérdida máxima contenida. Posición segura.",
        "pregunta": "¿Cuál es la máxima pérdida probable con X% de confianza?",
    },
    "black_scholes": {
        "polos": ("opción sin valor (muy out of the money)", "opción valiosa (deep in the money)"), "eje": "precio justo de un derecho futuro",
        "presupuestos": ["Volatilidad constante (no lo es)", "Sin dividendos en versión básica", "Mercados continuos y sin fricción"],
        "razonamiento": [("Calcular probabilidad de ejercicio (N(d1), N(d2))", "¿Cuán probable es que la opción acabe in the money?", "PROBABILIDAD"), ("Ponderar: precio actual × probabilidad de subir - precio ejercicio × probabilidad de cobrar", "Valor esperado descontado", "RESULTADO: precio justo de la opción")],
        "si_alto": "La opción es valiosa: alta probabilidad de ejercerla con beneficio.", "si_bajo": "La opción apenas vale: improbable que se ejerza con beneficio.",
        "pregunta": "¿Cuál es el precio justo de este derecho a comprar/vender en el futuro?",
    },

    # ============================================================
    # ECONOMETRÍA (restantes)
    # ============================================================
    "t_statistic": {
        "polos": ("no significativo (efecto ≈ ruido)", "significativo (efecto real)"), "eje": "señal/ruido",
        "presupuestos": ["Solo una normalización (NORMALIZAR) — la fórmula más simple de econometría", "p<0.05 es convención, no verdad absoluta"],
        "razonamiento": [("Dividir coeficiente por su error estándar", "¿Cuántas veces más grande es el efecto que su incertidumbre?", "RESULTADO: ratio señal/ruido")],
        "si_alto": "El efecto es grande relativo a la incertidumbre. Probablemente real.", "si_bajo": "El efecto es pequeño relativo a la incertidumbre. Podría ser ruido.",
        "pregunta": "¿Este efecto es real o podría ser casualidad?",
    },
    "p_valor": {
        "polos": ("efecto real (p bajo)", "posiblemente ruido (p alto)"), "eje": "evidencia contra la hipótesis nula",
        "presupuestos": ["NO es la probabilidad de que la hipótesis sea verdadera", "Es la probabilidad de ver estos datos SI el efecto fuera cero"],
        "razonamiento": [("Asumir que no hay efecto (H0)", "Mundo donde no pasa nada", "HIPÓTESIS nula"), ("Calcular probabilidad de ver datos tan extremos como los observados", "¿Cuán raro es lo que vi si no pasa nada?", "RESULTADO: cuán incompatibles son los datos con 'no pasa nada'")],
        "si_alto": "Los datos son compatibles con 'no pasa nada'. No hay evidencia suficiente.", "si_bajo": "Los datos son MUY incompatibles con 'no pasa nada'. Probablemente hay efecto real.",
        "pregunta": "¿Cuán probable es ver estos datos si realmente no hubiera efecto?",
    },
    "iv_2sls": {
        "polos": ("sin efecto causal", "efecto causal fuerte"), "eje": "efecto causal limpio",
        "presupuestos": ["Isomorfo con OLS (COMPONER→INVERTIR→COMPONER) — misma gramática, diferente pureza", "Requiere instrumento válido (relevante + exógeno) — el talón de Aquiles"],
        "razonamiento": [("Encontrar instrumento Z que afecta X pero no Y directamente", "Variable que 'empuja' X sin tocar Y", "INSTRUMENTO"), ("Primera etapa: predecir X con Z", "Purificar X de endogeneidad", "X limpia"), ("Segunda etapa: regresar Y sobre X limpia", "Efecto causal", "RESULTADO: cuánto cambia Y cuando X cambia por razones exógenas")],
        "si_alto": "X tiene efecto causal fuerte sobre Y. Cambiar X cambiaría Y.", "si_bajo": "X no causa Y (o el efecto es pequeño). La correlación era espuria.",
        "pregunta": "¿Cuál es el efecto CAUSAL de X sobre Y, limpio de endogeneidad?",
    },
    "control_sintetico": {
        "polos": ("sin efecto", "efecto grande"), "eje": "efecto causal por contrafactual construido",
        "presupuestos": ["Construye un 'clon' del tratado con combinación de controles", "No funciona si no hay buenos controles"],
        "razonamiento": [("Encontrar pesos óptimos para controles que repliquen al tratado pre-tratamiento", "Construir gemelo sintético", "CONTRAFACTUAL"), ("Comparar tratado con su gemelo post-tratamiento", "¿Qué habría pasado sin tratamiento?", "RESULTADO: efecto = diferencia entre real y sintético")],
        "si_alto": "El tratamiento tuvo efecto grande. El real diverge mucho de su gemelo.", "si_bajo": "El tratamiento no tuvo efecto. El real y su gemelo evolucionan igual.",
        "pregunta": "¿Qué habría pasado sin la intervención?",
    },
    "garch": {
        "polos": ("volatilidad baja y estable", "volatilidad alta y autoalimentada"), "eje": "volatilidad condicional",
        "presupuestos": ["La volatilidad de hoy depende de la volatilidad y shocks de ayer", "Captura clusters de volatilidad (periodos tranquilos y periodos turbulentos)"],
        "razonamiento": [("Tomar shock cuadrado del período anterior (ε²)", "¿Hubo sorpresa ayer?", "REACCIÓN a noticias"), ("Tomar volatilidad del período anterior (σ²)", "¿Era volátil ayer?", "PERSISTENCIA"), ("Ponderar y sumar", "Volatilidad de hoy = reacción + inercia + base", "RESULTADO: cuánto fluctuará hoy dado lo que pasó ayer")],
        "si_alto": "Período turbulento: la volatilidad se autoalimenta. Shocks grandes generan más volatilidad.", "si_bajo": "Período tranquilo: poca reacción a noticias, baja inercia.",
        "pregunta": "¿Cuánto fluctuará hoy dado lo que pasó ayer?",
    },

    # ============================================================
    # OPTIMIZACIÓN (restantes)
    # ============================================================
    "lagrangiano": {
        "polos": ("restricción inactiva (no muerde)", "restricción activa (limita el óptimo)"), "eje": "coste de la restricción",
        "presupuestos": ["λ (multiplicador) = precio sombra: cuánto mejoraría el óptimo si relajaras la restricción 1 unidad"],
        "razonamiento": [("Construir L = f(x) - λ·g(x)", "Objetivo - penalización por violar restricción", "FUNCIÓN AUXILIAR"), ("Derivar respecto a x: ∂f/∂x = λ·∂g/∂x", "En el óptimo, el gradiente del objetivo es proporcional al de la restricción", "CONDICIÓN"), ("λ = cuánto vale relajar la restricción", "Precio sombra", "RESULTADO: cuánto pagarías por una unidad más de recurso")],
        "si_alto": "La restricción muerde fuerte. Relajarla mejoraría mucho el resultado. Recurso escaso y valioso.", "si_bajo": "La restricción no muerde. Hay holgura. El recurso no es limitante.",
        "pregunta": "¿Cuánto mejoraría el resultado si tuviera una unidad más de recurso?",
    },
    "kkt": {
        "polos": ("interior (lejos de límites)", "frontera (en el límite)"), "eje": "naturaleza del óptimo",
        "presupuestos": ["Generalizan Lagrange a desigualdades", "Complementariedad: o la restricción muerde o su multiplicador es cero"],
        "razonamiento": [("Verificar condiciones de primer orden", "Gradiente = combinación de gradientes de restricciones", "NECESIDAD"), ("Verificar complementariedad", "Restricción activa ↔ multiplicador > 0", "SELECCIÓN de restricciones activas"), ("RESULTADO: qué restricciones limitan y cuáles son irrelevantes", "Mapa de cuellos de botella", "RESULTADO")],
        "si_alto": "El óptimo está en el borde. Las restricciones importan.", "si_bajo": "El óptimo está en el interior. Las restricciones no limitan.",
        "pregunta": "¿Qué restricciones limitan el óptimo y cuáles son irrelevantes?",
    },

    # ============================================================
    # CONDUCTUAL (restantes)
    # ============================================================
    "descuento_hiperbolico": {
        "polos": ("paciente (descuenta poco)", "impaciente (descuenta mucho)"), "eje": "impaciencia inconsistente",
        "presupuestos": ["A diferencia del descuento exponencial, las preferencias CAMBIAN con el tiempo", "Hoy prefiero €100 hoy a €110 mañana, pero prefiero €110 en 31 días a €100 en 30"],
        "razonamiento": [("Multiplicar utilidad futura por 1/(1+kt)", "Descontar el futuro", "DESCUENTO"), ("A diferencia de δ^t (exponencial), 1/(1+kt) desciende rápido al principio y lento después", "El presente es DESPROPORCIONADAMENTE más valioso", "INCONSISTENCIA"), ("RESULTADO: explica procrastinación, adicción, falta de ahorro", "Sesgo presente", "RESULTADO")],
        "si_alto": "Muy impaciente: el presente domina cualquier decisión. Incapaz de comprometerse con el futuro.", "si_bajo": "Relativamente paciente: capaz de sacrificar hoy por mañana.",
        "pregunta": "¿Cuánto devalúa el futuro de forma inconsistente?",
    },
    "prospect_theory_weighting": {
        "polos": ("objetivo (percibe probabilidades correctamente)", "distorsionado (sobrepondera raras, infrapondera frecuentes)"), "eje": "distorsión probabilística",
        "presupuestos": ["La gente sobrepondera eventos raros (comprar lotería) e infrapondera eventos frecuentes (no comprar seguro)"],
        "razonamiento": [("Transformar probabilidad objetiva por función w(p)", "Distorsionar percepción", "SESGO"), ("Sobreponderar colas (p pequeña → w(p) > p)", "Los eventos raros parecen más probables de lo que son", "RESULTADO: por qué compramos lotería y no seguro")],
        "si_alto": "Percepción distorsionada: eventos raros parecen comunes, comunes parecen raros.", "si_bajo": "Percepción calibrada: evalúa probabilidades correctamente.",
        "pregunta": "¿Cuánto distorsiona la percepción de probabilidades?",
    },

    # ============================================================
    # MATEMÁTICA PURA (restantes)
    # ============================================================
    "punto_fijo_brouwer": {
        "polos": ("sin equilibrio (no hay punto fijo)", "equilibrio existe (hay punto fijo)"), "eje": "existencia de solución",
        "presupuestos": ["Solo garantiza EXISTENCIA, no unicidad ni estabilidad", "Requiere compacidad + convexidad + continuidad"],
        "razonamiento": [("Verificar que el espacio es compacto y convexo", "¿El problema está bien definido?", "CONDICIÓN"), ("Verificar que la función es continua", "¿Las respuestas cambian suavemente?", "CONDICIÓN"), ("EXISTE punto donde f(x*)=x*", "La función se reproduce a sí misma", "RESULTADO: el equilibrio existe (aunque no sepamos dónde)")],
        "si_alto": "Condiciones cumplidas: equilibrio existe. Buscar es fructífero.", "si_bajo": "Condiciones no cumplidas: el equilibrio puede no existir. No buscar a ciegas.",
        "pregunta": "¿Existe un equilibrio en este sistema?",
    },
    "contraccion_banach": {
        "polos": ("no converge (diverge)", "converge (al punto fijo)"), "eje": "convergencia algorítmica",
        "presupuestos": ["Más fuerte que Brouwer: existencia + unicidad + convergencia + algoritmo", "Requiere contracción: cada iteración acerca al punto fijo"],
        "razonamiento": [("Verificar que cada iteración reduce la distancia en factor β<1", "¿Se acerca?", "CONTRACCIÓN"), ("Iterar: T(T(T(...x₀)))", "Repetir", "ALGORITMO"), ("RESULTADO: converge al ÚNICO punto fijo", "Garantía triple", "RESULTADO")],
        "si_alto": "Converge rápido (β pequeño). Pocas iteraciones necesarias.", "si_bajo": "Converge lento (β cercano a 1). Muchas iteraciones.",
        "pregunta": "¿Este proceso iterativo converge y a qué velocidad?",
    },
    "lln": {
        "polos": ("datos insuficientes (muestra pequeña)", "datos revelan la verdad (muestra grande)"), "eje": "convergencia a la realidad",
        "presupuestos": ["Requiere independencia", "No dice cuán rápido converge (eso es el TCL)"],
        "razonamiento": [("Acumular observaciones", "Más datos", "ACUMULACIÓN"), ("La media muestral converge a la esperanza", "Los datos revelan la verdad", "RESULTADO: con suficientes datos, sabrás la respuesta correcta")],
        "si_alto": "Muestra grande: la media muestral ES (casi) la real. Confía en los datos.", "si_bajo": "Muestra pequeña: la media muestral puede estar lejos de la real. No confíes aún.",
        "pregunta": "¿Tengo suficientes datos para que la media muestral sea fiable?",
    },
    "tcl": {
        "polos": ("distribución desconocida", "distribución normal"), "eje": "normalidad asintótica",
        "presupuestos": ["Funciona con CUALQUIER distribución original (si tiene varianza finita)", "La velocidad de convergencia depende de la distribución original"],
        "razonamiento": [("Tomar medias de muestras repetidas", "Distribución de medias muestrales", "DISTRIBUCIÓN del estimador"), ("Con n grande, esta distribución se parece a una normal", "Campana de Gauss", "FORMA"), ("RESULTADO: puedes usar intervalos de confianza y tests normales", "Inferencia estadística", "RESULTADO")],
        "si_alto": "n grande: la distribución es normal. Tests estándar son válidos.", "si_bajo": "n pequeño: la distribución puede no ser normal. Tests pueden ser incorrectos.",
        "pregunta": "¿Puedo usar estadística normal para hacer inferencia?",
    },
    "jensen": {
        "polos": ("función lineal (igualdad)", "función convexa/cóncava (desigualdad estricta)"), "eje": "efecto de la curvatura",
        "presupuestos": ["Fundamental para entender aversión al riesgo", "Si u es cóncava: E[u(X)] < u(E[X]) → la gente prefiere la certeza"],
        "razonamiento": [("Aplicar función convexa/cóncava a variable aleatoria", "Transformar", "TRANSFORMACIÓN"), ("Comparar E[f(X)] con f(E[X])", "¿La esperanza de la transformación = transformación de la esperanza?", "COMPARACIÓN"), ("NO: la curvatura crea gap", "El gap ES la prima de riesgo", "RESULTADO: por qué los aversos al riesgo pagan seguro")],
        "si_alto": "Gran curvatura: gran desigualdad. Las personas pagan mucho por certeza.", "si_bajo": "Poca curvatura (casi lineal): poca diferencia entre riesgo y certeza.",
        "pregunta": "¿Cuánto afecta la curvatura de las preferencias a las decisiones bajo riesgo?",
    },
}

SEMANTICA.update(SEMANTICA_2)

# ============================================================
# SEMÁNTICA DE LAS 62 FEATURES DE LOS 10 MARCOS DEL SIMBIONTE
# ============================================================
# Estas son las fórmulas que el Simbionte calcula INTERNAMENTE.
# El LLM las necesita para VERIFICAR el razonamiento del Simbionte.

SEMANTICA_MARCOS = {
    # === EJE 1: ESTADÍSTICA (8 features) ===
    "marco_entropia": {"polos":("concentrado en pocos tipos","diverso en muchos tipos"),"eje":"diversidad funcional","presupuestos":["Usa log₂ — mide en bits","Máxima cuando todos los tipos son igual de frecuentes","No distingue qué tipos son — solo cuántos hay"],"razonamiento":[("Normalizar frecuencias a probabilidades","¿Qué fracción es cada tipo?","DISTRIBUCIÓN"),("Aplicar -Σp·log₂(p)","Lo frecuente pesa poco, lo raro mucho","RESULTADO: bits de sorpresa")],"si_alto":"Muchos tipos diferentes, ninguno domina. Discurso rico y variado.","si_bajo":"Pocos tipos o uno domina. Discurso repetitivo o monotemático.","pregunta":"¿Cuánta variedad de funciones sintácticas usa el texto?"},
    "marco_diversidad": {"polos":("usa pocos tipos","usa muchos tipos"),"eje":"riqueza tipológica","presupuestos":["Solo cuenta tipos únicos, no frecuencia","Normalizada por tipos posibles"],"razonamiento":[("Contar tipos únicos observados","¿Cuántos tipos diferentes aparecen?","N_únicos"),("Dividir por tipos posibles","Relativizar","RESULTADO: proporción de tipos usados")],"si_alto":"Usa la mayoría de los tipos disponibles. Repertorio amplio.","si_bajo":"Usa muy pocos tipos del total posible. Repertorio limitado.","pregunta":"¿Cuántos tipos diferentes del total posible usa?"},
    "marco_concentracion": {"polos":("igualitario","concentrado"),"eje":"concentración de frecuencias","presupuestos":["Gini simplificado (1-Σp²)","No distingue arriba de abajo"],"razonamiento":[("Elevar cada probabilidad al cuadrado","Amplificar los frecuentes","PONDERACIÓN"),("Sumar e invertir","1 = perfecto, 0 = un tipo domina todo","RESULTADO: grado de dispersión")],"si_alto":"Las frecuencias están distribuidas. Sin dominancia.","si_bajo":"Un tipo o pocos acaparan la mayoría de ocurrencias.","pregunta":"¿Se concentran las ocurrencias en pocos tipos o se distribuyen?"},
    "marco_dominante": {"polos":("sin dominante","uno domina claramente"),"eje":"dominancia","presupuestos":["Solo mira el máximo — ignora distribución completa"],"razonamiento":[("Encontrar la frecuencia más alta","¿Qué proporción tiene el tipo más frecuente?","RESULTADO: peso del dominante")],"si_alto":"Un solo tipo ocupa >30% del discurso. Dominancia clara.","si_bajo":"Ningún tipo destaca significativamente. Equilibrio.","pregunta":"¿Hay un tipo que domine sobre los demás?"},
    "marco_top2": {"polos":("disperso","bipolar"),"eje":"bipolaridad","presupuestos":["Solo mira los 2 más frecuentes — ignora el resto"],"razonamiento":[("Sumar frecuencias de los 2 tipos más frecuentes","¿Cuánto acaparan los 2 principales?","RESULTADO: grado de bipolaridad")],"si_alto":"Los 2 tipos principales acaparan la mayoría. Estructura bipolar.","si_bajo":"No hay 2 tipos dominantes. Estructura distribuida.","pregunta":"¿El discurso se polariza entre dos tipos principales?"},
    "marco_asimetria": {"polos":("cola izquierda","cola derecha"),"eje":"asimetría distribucional","presupuestos":["Skewness sobre distribución de frecuencias","Amplifica extremos con cubo"],"razonamiento":[("Calcular skewness de las frecuencias","¿Hay más tipos raros o más frecuentes?","RESULTADO: dirección de la cola")],"si_alto":"Muchos tipos raros con pocos frecuentes. Cola derecha.","si_bajo":"Pocos tipos raros con muchos frecuentes. Cola izquierda.","pregunta":"¿La distribución de tipos se inclina hacia los raros o los frecuentes?"},
    "marco_curtosis": {"polos":("sin extremos","colas pesadas"),"eje":"riesgo de extremos tipológicos","presupuestos":["Kurtosis sobre frecuencias","4ª potencia amplifica extremos brutalmente"],"razonamiento":[("Calcular kurtosis de frecuencias","¿Cuán probable es un tipo muy dominante o muy raro?","RESULTADO: peso de las colas")],"si_alto":"Hay tipos con frecuencias extremas (muy altas o muy bajas). Distribución puntiaguda.","si_bajo":"Las frecuencias son regulares. Distribución plana.","pregunta":"¿Hay tipos con frecuencias extremadamente altas o bajas?"},
    "marco_raros": {"polos":("sin rarezas","muchas rarezas"),"eje":"riqueza marginal","presupuestos":["Umbral fijo: raro = <5% de ocurrencias","No mide cuán raros son — solo cuántos son raros"],"razonamiento":[("Contar tipos con frecuencia <5%","¿Cuántos tipos aparecen raramente?","N_raros"),("Dividir por total de tipos","Relativizar","RESULTADO: proporción de tipos raros")],"si_alto":"Muchos tipos aparecen raramente. Texto atípico o con muchos matices.","si_bajo":"Pocos tipos raros. Texto convencional.","pregunta":"¿Cuántos tipos funcionales son infrecuentes?"},

    # === EJE 2: CONJUNTOS (5 features) ===
    "marco_jaccard": {"polos":("mitades completamente diferentes","mitades idénticas"),"eje":"consistencia temporal","presupuestos":["Compara primera y segunda mitad","Solo mira presencia/ausencia, no frecuencia"],"razonamiento":[("Calcular tipos en primera y segunda mitad","¿Qué usa cada mitad?","CONJUNTOS"),("Intersección/Unión","¿Cuánto comparten?","RESULTADO: grado de similitud entre mitades")],"si_alto":"Ambas mitades usan los mismos tipos. Discurso consistente.","si_bajo":"Cada mitad usa tipos diferentes. Hay un giro o cambio.","pregunta":"¿La primera y segunda mitad del texto usan las mismas funciones?"},
    "marco_exclusivas_a": {"polos":("todo compartido","la 1ª mitad tiene tipos únicos"),"eje":"innovación de la primera mitad","presupuestos":["Mide asimetría direccional A→B"],"razonamiento":[("Tipos en A que no están en B, dividir por |A|","¿Cuánto de A es exclusivo?","RESULTADO: proporción exclusiva de A")],"si_alto":"La primera mitad introduce tipos que la segunda abandona.","si_bajo":"Todo lo que usa la primera mitad también lo usa la segunda.","pregunta":"¿La primera mitad tiene funciones que la segunda no usa?"},
    "marco_exclusivas_b": {"polos":("todo compartido","la 2ª mitad tiene tipos únicos"),"eje":"innovación de la segunda mitad","presupuestos":["Simétrico a exclusivas_a pero en dirección B→A"],"razonamiento":[("Tipos en B que no están en A, dividir por |B|","¿Cuánto de B es exclusivo?","RESULTADO")],"si_alto":"La segunda mitad introduce tipos nuevos. Evolución del discurso.","si_bajo":"La segunda mitad no innova respecto a la primera.","pregunta":"¿La segunda mitad introduce funciones que la primera no tenía?"},
    "marco_cobertura": {"polos":("no cubre nada","cubre todo"),"eje":"cobertura de referencia","presupuestos":["Mide cuánto de B está cubierto por A"],"razonamiento":[("Intersección / |B|","¿Qué proporción de la referencia está presente?","RESULTADO: cobertura")],"si_alto":"La primera mitad contiene casi todo lo que tiene la segunda.","si_bajo":"La primera mitad cubre poco de la segunda. Gran diferencia.","pregunta":"¿Cuánto de lo que aparece al final ya estaba al principio?"},
    "marco_simetria_conj": {"polos":("muy asimétrico","perfectamente simétrico"),"eje":"equilibrio entre mitades","presupuestos":["Mide diferencia absoluta de exclusivas"],"razonamiento":[("Calcular |exclusivas_A - exclusivas_B| / |A∪B|","¿La asimetría es en una dirección?","DESEQUILIBRIO"),("1 - desequilibrio","Invertir","RESULTADO: grado de simetría")],"si_alto":"Ambas mitades son igual de diferentes entre sí. Equilibrio.","si_bajo":"Una mitad tiene mucho más contenido exclusivo que la otra.","pregunta":"¿Las dos mitades del texto son simétricas en contenido?"},

    # === EJE 3: GRAFOS (8 features) ===
    "marco_profundidad": {"polos":("superficial (1 nivel)","profundo (muchos niveles)"),"eje":"profundidad de razonamiento","presupuestos":["Longest path normalizado","En DAG = cadena lógica más larga"],"razonamiento":[("Encontrar camino más largo en el grafo de transiciones","¿Cuántos pasos tiene la cadena más larga?","PROFUNDIDAD"),("Normalizar por n nodos","Relativizar","RESULTADO: profundidad relativa")],"si_alto":"Razonamiento encadenado largo. Muchos pasos lógicos.","si_bajo":"Razonamiento plano. Pocos encadenamientos.","pregunta":"¿Cuán profundo es el encadenamiento del razonamiento?"},
    "marco_grado_medio": {"polos":("nodos aislados","nodos muy conectados"),"eje":"conectividad","presupuestos":["Grado medio del grafo dirigido"],"razonamiento":[("Contar conexiones de cada nodo","¿Con cuántos se relaciona cada tipo?","GRADO"),("Promediar","Media de conexiones","RESULTADO: conectividad media")],"si_alto":"Los tipos están muy interconectados. Red densa.","si_bajo":"Los tipos están aislados. Red fragmentada.","pregunta":"¿Cuán conectados están los tipos funcionales entre sí?"},
    "marco_betweenness": {"polos":("sin cuello de botella","cuello de botella claro"),"eje":"centralidad de intermediación","presupuestos":["Betweenness centrality máxima","Un nodo que todos deben cruzar"],"razonamiento":[("Calcular betweenness de cada nodo","¿Quién está en el camino entre todos?","INTERMEDIACIÓN"),("Tomar el máximo","¿Hay un nodo que conecta todo?","RESULTADO: grado de cuello de botella")],"si_alto":"Un tipo funcional conecta TODO. Si falla, la estructura se rompe.","si_bajo":"No hay cuello de botella. La información fluye por múltiples caminos.","pregunta":"¿Hay un nodo que centraliza toda la comunicación?"},
    "marco_n_componentes": {"polos":("todo conectado","fragmentado"),"eje":"fragmentación","presupuestos":["Componentes weakly connected"],"razonamiento":[("Contar componentes conexas","¿En cuántas islas se divide el grafo?","RESULTADO: grado de fragmentación")],"si_alto":"Pensamiento fragmentado en múltiples líneas desconectadas.","si_bajo":"Todo conectado en una sola estructura.","pregunta":"¿El razonamiento está conectado o fragmentado en islas?"},
    "marco_densidad": {"polos":("grafo disperso","grafo denso"),"eje":"densidad de conexiones","presupuestos":["edges/possible_edges"],"razonamiento":[("Contar aristas reales / aristas posibles","¿Qué proporción de conexiones posibles existen?","RESULTADO: densidad")],"si_alto":"Casi todas las conexiones posibles existen. Todo se relaciona con todo.","si_bajo":"Pocas conexiones del total posible. Estructura selectiva.","pregunta":"¿Cuán densa es la red de relaciones?"},
    "marco_ratio_hojas": {"polos":("sin callejones","muchos callejones"),"eje":"terminaciones","presupuestos":["Nodos sin sucesores (out-degree=0)"],"razonamiento":[("Contar nodos terminales / total","¿Cuántos tipos no llevan a ningún otro?","RESULTADO: proporción de finales")],"si_alto":"Muchos tipos son callejones sin salida. El discurso llega a muchos finales.","si_bajo":"Pocos finales. El discurso fluye sin cerrarse.","pregunta":"¿Cuántos tipos funcionales son puntos finales (no llevan a nada)?"},
    "marco_reciprocidad": {"polos":("unidireccional","bidireccional"),"eje":"mutualidad","presupuestos":["Proporción de aristas con reversa"],"razonamiento":[("Contar aristas bidireccionales / total","¿Cuántas relaciones van en ambas direcciones?","RESULTADO: mutualidad")],"si_alto":"Las relaciones son mutuas. A→B implica B→A.","si_bajo":"Las relaciones son unidireccionales. Jerarquía clara.","pregunta":"¿Las relaciones entre tipos son mutuas o unidireccionales?"},
    "marco_clustering": {"polos":("vecinos desconectados","vecinos interconectados"),"eje":"agrupamiento local","presupuestos":["Clustering medio sobre grafo no dirigido"],"razonamiento":[("Para cada nodo, ¿qué proporción de sus vecinos son vecinos entre sí?","Triángulos locales","LOCAL"),("Promediar","Media de agrupamiento","RESULTADO: cohesión local")],"si_alto":"Los vecinos de cada tipo se conocen entre sí. Clusters densos.","si_bajo":"Los vecinos no se relacionan entre sí. Sin clusters.","pregunta":"¿Los tipos que se relacionan con un mismo tipo se relacionan entre sí?"},

    # === EJE 4: MARKOV (7 features) ===
    "marco_h_dist": {"polos":("pocos estados","muchos estados equiprobables"),"eje":"diversidad de estados","presupuestos":["Entropía de la distribución estacionaria empírica"],"razonamiento":[("Calcular entropía de las frecuencias de estados","¿Cuántos estados diferentes visita?","RESULTADO: diversidad de estados")],"si_alto":"Visita muchos estados diferentes por igual.","si_bajo":"Se concentra en pocos estados.","pregunta":"¿Cuánta diversidad de estados tiene la secuencia?"},
    "marco_h_trans": {"polos":("transiciones predecibles","transiciones impredecibles"),"eje":"incertidumbre de transición","presupuestos":["Entropía condicional de la matriz de transición"],"razonamiento":[("Para cada estado, calcular entropía de a dónde va","¿Cuán predecible es el siguiente estado?","INCERTIDUMBRE por estado"),("Ponderar por frecuencia de cada estado","Media ponderada","RESULTADO: incertidumbre de transición global")],"si_alto":"Desde cada estado, podría ir a muchos otros. Impredecible.","si_bajo":"Desde cada estado, casi siempre va al mismo sitio. Predecible.","pregunta":"¿Cuán predecible es la siguiente transición dado el estado actual?"},
    "marco_estructura": {"polos":("secuencia aleatoria","secuencia muy estructurada"),"eje":"estructura secuencial","presupuestos":["h_dist - h_trans: entropía total menos condicional","Lo que se gana sabiendo el estado actual"],"razonamiento":[("Calcular h_dist (diversidad total)","¿Cuánta variación hay?","TOTAL"),("Restar h_trans (incertidumbre condicional)","¿Cuánta se explica por la posición?","RESULTADO: información estructural")],"si_alto":"Saber dónde estás te dice MUCHO sobre dónde irás. Secuencia estructurada.","si_bajo":"Saber dónde estás no ayuda a predecir. Secuencia aleatoria.","pregunta":"¿Cuánta estructura tiene la secuencia (vs aleatorio)?"},
    "marco_diagonal": {"polos":("alta variedad (cambia mucho)","monotonía (repite)"),"eje":"inercia secuencial","presupuestos":["Media de la diagonal de la matriz de transición","Diagonal alta = tendencia a permanecer en el mismo estado"],"razonamiento":[("Promediar P(i→i) para todos los estados","¿Cuán probable es quedarse en el mismo estado?","RESULTADO: grado de monotonía")],"si_alto":"Tiende a repetir el mismo tipo. Discurso monótono o focalizado.","si_bajo":"Cambia de tipo frecuentemente. Discurso dinámico o errático.","pregunta":"¿El discurso tiende a repetir el mismo tipo o cambia constantemente?"},
    "marco_est_0": {"polos":("nunca en estado 0","siempre en estado 0"),"eje":"peso estacionario del estado 0","presupuestos":["Componente 0 de la distribución estacionaria"],"razonamiento":[("Calcular distribución de largo plazo de la cadena","¿A dónde converge?","ESTACIONARIA"),("Tomar componente 0","Peso del primer estado","RESULTADO")],"si_alto":"El sistema pasa mucho tiempo en el estado 0.","si_bajo":"El sistema raramente está en estado 0.","pregunta":"¿Cuánto tiempo pasa el sistema en el estado 0?"},
    "marco_est_1": {"polos":("nunca en estado 1","siempre en estado 1"),"eje":"peso estacionario del estado 1","presupuestos":["Componente 1"],"razonamiento":[("Tomar componente 1 de la distribución estacionaria","Peso del segundo estado","RESULTADO")],"si_alto":"El sistema gravita hacia el estado 1.","si_bajo":"El estado 1 es raro en el largo plazo.","pregunta":"¿Cuánto tiempo pasa en el estado 1?"},
    "marco_est_2": {"polos":("nunca en estado 2","siempre en estado 2"),"eje":"peso estacionario del estado 2","presupuestos":["Componente 2"],"razonamiento":[("Tomar componente 2","Peso del tercer estado","RESULTADO")],"si_alto":"El estado 2 domina en el largo plazo.","si_bajo":"El estado 2 es marginal.","pregunta":"¿Cuánto tiempo pasa en el estado 2?"},

    # === EJE 5: JUEGOS (6 features) ===
    "marco_n_agentes": {"polos":("monólogo (1 agente)","conflicto multipartito (muchos agentes)"),"eje":"complejidad del conflicto","presupuestos":["Proxy: tipos únicos en la secuencia","Más tipos = más 'jugadores' en el discurso"],"razonamiento":[("Contar tipos únicos","¿Cuántas 'voces' hay?","RESULTADO: número de agentes")],"si_alto":"Muchos agentes/posiciones en juego. Conflicto complejo.","si_bajo":"Pocos agentes. Discurso simple o monológico.","pregunta":"¿Cuántos agentes/posiciones diferentes compiten?"},
    "marco_n_condicionales": {"polos":("sin condicionales","muchas estrategias condicionales"),"eje":"sofisticación estratégica","presupuestos":["Proxy: cambios bruscos en la secuencia"],"razonamiento":[("Contar transiciones entre tipos diferentes","¿Cuántas veces cambia de estrategia?","RESULTADO: sofisticación")],"si_alto":"Muchos cambios de estrategia. Discurso que responde y se adapta.","si_bajo":"Pocas adaptaciones. Estrategia fija.","pregunta":"¿Cuántas estrategias condicionales hay?"},
    "marco_cruce": {"polos":("sin cruce (no hay Nash)","cruce detectado (Nash posible)"),"eje":"potencial de equilibrio","presupuestos":["Requiere ≥2 agentes × ≥2 condicionales","Nash = punto donde nadie mejora cambiando"],"razonamiento":[("¿Hay ≥2 agentes con ≥2 condicionales?","¿Las estrategias se cruzan?","RESULTADO: 1 si hay cruce, 0 si no")],"si_alto":"Condicionales cruzados: cada agente responde al otro. Nash posible.","si_bajo":"Sin cruce. Los agentes no interactúan estratégicamente.","pregunta":"¿Hay potencial de equilibrio de Nash (estrategias cruzadas)?"},
    "marco_simetria_juego": {"polos":("asimétrico (uno domina)","simétrico (poder equilibrado)"),"eje":"balance de poder","presupuestos":["Mide igualdad de peso entre agentes"],"razonamiento":[("Calcular proporción de cada agente","¿Cuánto espacio ocupa cada uno?","DISTRIBUCIÓN"),("Medir desviación estándar","¿Cuánta diferencia hay?","RESULTADO: simetría")],"si_alto":"Los agentes tienen peso similar. Conflicto equilibrado.","si_bajo":"Un agente domina. Asimetría de poder.","pregunta":"¿Los agentes tienen poder similar o uno domina?"},
    "marco_alternancia": {"polos":("sin tensión (flujo continuo)","máxima tensión (ping-pong)"),"eje":"tensión del conflicto","presupuestos":["Proporción de transiciones entre tipos diferentes"],"razonamiento":[("Contar cambios / total transiciones","¿Cuántas veces cambia?","RESULTADO: grado de tensión")],"si_alto":"Alta alternancia entre tipos. Tensión, debate, conflicto activo.","si_bajo":"Poca alternancia. Flujo continuo sin confrontación.","pregunta":"¿Hay tensión/conflicto activo en la secuencia?"},
    "marco_completitud": {"polos":("pocas combinaciones","todas las combinaciones"),"eje":"exhaustividad estratégica","presupuestos":["Pares reales / pares posibles"],"razonamiento":[("Contar combinaciones de transición observadas","¿Cuántas combinaciones se exploran?","EXPLORACIÓN"),("Dividir por posibles","Relativizar","RESULTADO: exhaustividad")],"si_alto":"Se exploran muchas combinaciones. Análisis exhaustivo.","si_bajo":"Pocas combinaciones exploradas. Análisis parcial.","pregunta":"¿Cuántas combinaciones estratégicas se exploran?"},

    # === EJE 6: CIBERNÉTICA (5 features) ===
    "marco_n_ciclos": {"polos":("sin loops","muchos loops de feedback"),"eje":"complejidad de retroalimentación","presupuestos":["Simple cycles en grafo de transiciones","Limitado a 100 para evitar explosión"],"razonamiento":[("Encontrar ciclos en el grafo","¿Cuántos loops hay?","RESULTADO: complejidad de feedback")],"si_alto":"Sistema muy interconectado con muchos loops. Difícil de predecir.","si_bajo":"Sistema lineal sin loops. Predecible.","pregunta":"¿Cuántos loops de retroalimentación tiene el sistema?"},
    "marco_prof_ciclo": {"polos":("ciclos cortos","ciclos largos"),"eje":"profundidad de los loops","presupuestos":["Media de longitud de ciclos"],"razonamiento":[("Promediar longitud de ciclos","¿Cuán largos son los loops?","RESULTADO")],"si_alto":"Los loops son largos. Efectos tardíos e indirectos.","si_bajo":"Los loops son cortos. Efectos inmediatos y directos.","pregunta":"¿Cuán largos son los ciclos de retroalimentación?"},
    "marco_amplificacion": {"polos":("sin amplificación","hay feedback positivo"),"eje":"amplificación","presupuestos":["1 si hay tipo repetido dentro de un ciclo","Feedback positivo = espiral (puede ser virtuosa o viciosa)"],"razonamiento":[("Buscar ciclos con repetición de tipo","¿Un mismo tipo se retroalimenta?","RESULTADO: 1 = espiral detectada")],"si_alto":"ESPIRAL detectada. El sistema se autoamplifica. Puede crecer exponencialmente o colapsar.","si_bajo":"Sin autoamplificación. Sistema estable.","pregunta":"¿El sistema se autoamplifica (feedback positivo)?"},
    "marco_regulacion": {"polos":("sin regulación","hay feedback negativo"),"eje":"autorregulación","presupuestos":["1 si hay ciclo con todos los tipos distintos","Feedback negativo = freno, vuelta al equilibrio"],"razonamiento":[("Buscar ciclos con tipos todos diferentes","¿Hay mecanismo de freno?","RESULTADO: 1 = regulación detectada")],"si_alto":"Mecanismo de freno detectado. El sistema corrige desviaciones.","si_bajo":"Sin freno. Si se desvía, no vuelve.","pregunta":"¿El sistema tiene mecanismo de autorregulación (feedback negativo)?"},
    "marco_ratio_feedback": {"polos":("regulación dominante","amplificación dominante"),"eje":"balance amplificación/regulación","presupuestos":["Proporción de ciclos amplificadores vs total"],"razonamiento":[("N ciclos con repetición / N ciclos total","¿Qué proporción amplifica vs regula?","RESULTADO")],"si_alto":"La mayoría de loops amplifica. Sistema en escalada.","si_bajo":"La mayoría de loops regula. Sistema estable.","pregunta":"¿Domina la amplificación o la regulación?"},

    # === EJE 7: SISTEMAS (6 features) ===
    "marco_prof_max": {"polos":("sin anidación","muy anidado"),"eje":"profundidad máxima de anidación","presupuestos":["Longest run consecutivo del mismo tipo"],"razonamiento":[("Encontrar la secuencia consecutiva más larga del mismo tipo","¿Cuán profunda es la recursión?","RESULTADO")],"si_alto":"Hay bloques muy largos del mismo tipo. Estructura profundamente anidada.","si_bajo":"Bloques cortos. Estructura plana.","pregunta":"¿Cuán profundamente se anidan los subsistemas?"},
    "marco_prof_media": {"polos":("bloques cortos","bloques largos"),"eje":"tamaño medio de subsistemas","presupuestos":["Media de longitudes de runs"],"razonamiento":[("Promediar longitudes de bloques consecutivos","¿Cuán grandes son los bloques típicos?","RESULTADO")],"si_alto":"Subsistemas grandes. Pocas transiciones, bloques densos.","si_bajo":"Subsistemas pequeños. Muchas transiciones, granularidad fina.","pregunta":"¿Cuán grandes son los subsistemas típicos?"},
    "marco_n_subsistemas": {"polos":("monolítico","muy fragmentado"),"eje":"complejidad estructural","presupuestos":["Número de bloques contiguos del mismo tipo"],"razonamiento":[("Contar bloques","¿En cuántas partes se divide?","RESULTADO")],"si_alto":"Muchas partes. Sistema complejo con muchos subsistemas.","si_bajo":"Pocas partes. Sistema simple o monolítico.","pregunta":"¿Cuántos subsistemas tiene la estructura?"},
    "marco_equilibrio": {"polos":("muy desigual","equilibrado"),"eje":"equilibrio entre subsistemas","presupuestos":["1 - CV de tamaños de bloques"],"razonamiento":[("Calcular desviación estándar de tamaños / media","¿Cuánta diferencia hay entre bloques?","VARIABILIDAD"),("Invertir","Equilibrio = poca variabilidad","RESULTADO")],"si_alto":"Subsistemas de tamaño similar. Estructura equilibrada.","si_bajo":"Subsistemas muy desiguales. Uno domina o uno es marginal.","pregunta":"¿Los subsistemas son de tamaño similar?"},
    "marco_emergencia": {"polos":("no hay emergencia","la conclusión es nueva"),"eje":"emergencia","presupuestos":["1 si el tipo final NO está en los subsistemas anteriores","Emergencia = propiedad del todo que no está en las partes"],"razonamiento":[("Verificar si el tipo final aparece antes","¿La conclusión estaba ya en las premisas?","TEST"),("Si no aparece → emergencia","La conclusión es NUEVA — no se deduce de lo anterior","RESULTADO")],"si_alto":"La conclusión no estaba en las premisas. Salto lógico o creativo.","si_bajo":"La conclusión ya estaba implícita en lo anterior. Deducción pura.","pregunta":"¿La conclusión emerge como algo nuevo o se deduce de lo anterior?"},
    "marco_coherencia_sis": {"polos":("incoherente","coherente"),"eje":"coherencia entre partes","presupuestos":["Proporción de subsistemas consecutivos del mismo tipo"],"razonamiento":[("Contar transiciones donde el tipo no cambia","¿Las partes consecutivas son del mismo tipo?","RESULTADO")],"si_alto":"Subsistemas consecutivos son coherentes. Estructura fluida.","si_bajo":"Cada subsistema es diferente al anterior. Estructura fragmentada.","pregunta":"¿Las partes del sistema son coherentes entre sí?"},

    # === EJE 8: TOPOLOGÍA (6 features) ===
    "marco_n_comp_topo": {"polos":("todo conectado","fragmentado"),"eje":"fragmentación topológica","presupuestos":["Componentes weakly connected del grafo de transiciones"],"razonamiento":[("Contar islas en el grafo","¿En cuántas piezas se divide?","RESULTADO")],"si_alto":"Estructura fragmentada en varias piezas desconectadas.","si_bajo":"Todo conectado en una pieza.","pregunta":"¿La estructura está en una pieza o fragmentada?"},
    "marco_agujeros": {"polos":("completo","con gaps"),"eje":"completitud funcional","presupuestos":["Funciones posibles menos presentes","Gap = función que debería estar pero no está"],"razonamiento":[("Contar tipos posibles - tipos observados","¿Cuántos faltan?","RESULTADO: número de agujeros")],"si_alto":"Muchas funciones esperadas están AUSENTES. Gaps en la argumentación.","si_bajo":"Casi todas las funciones presentes. Argumentación completa.","pregunta":"¿Cuántas funciones esperadas faltan?"},
    "marco_ratio_agujeros": {"polos":("sin gaps","lleno de gaps"),"eje":"proporción de ausencias","presupuestos":["Agujeros / tipos posibles"],"razonamiento":[("Normalizar agujeros por tipos posibles","¿Qué proporción falta?","RESULTADO")],"si_alto":"Gran proporción de funciones ausentes. Estructura incompleta.","si_bajo":"Casi todo presente. Estructura completa.","pregunta":"¿Qué proporción de funciones falta?"},
    "marco_compacidad": {"polos":("disperso","compacto"),"eje":"compacidad","presupuestos":["1 - CV de frecuencias no nulas","Compacto = las funciones presentes tienen frecuencias similares"],"razonamiento":[("Medir variabilidad de frecuencias","¿Las funciones presentes se usan por igual?","VARIABILIDAD"),("Invertir","Compacidad = poca variabilidad","RESULTADO")],"si_alto":"Las funciones presentes se usan de forma equilibrada. Argumento compacto.","si_bajo":"Unas funciones se usan mucho más que otras. Argumento disperso.","pregunta":"¿Las funciones presentes se usan equilibradamente?"},
    "marco_persistencia_topo": {"polos":("frágil (depende de una pieza)","robusto (sobrevive sin la principal)"),"eje":"robustez","presupuestos":["Quitar el tipo más frecuente y ver qué sobrevive","Persistencia alta = la estructura NO depende de un solo tipo"],"razonamiento":[("Quitar tipo más frecuente","Perturbar la estructura","TEST"),("¿Cuántos tipos sobreviven?","Robustez","RESULTADO: proporción que sobrevive")],"si_alto":"Quitar la pieza principal no destruye la estructura. Robusto.","si_bajo":"Quitar la pieza principal destruye casi todo. Frágil.","pregunta":"¿Cuán robusto es el patrón si quitas la pieza más importante?"},
    "marco_convexidad": {"polos":("espacio hueco","espacio convexo"),"eje":"convexidad del espacio","presupuestos":["Pares de transición reales / pares posibles"],"razonamiento":[("Contar combinaciones de transición observadas / posibles","¿El espacio está lleno o tiene huecos?","RESULTADO")],"si_alto":"El espacio de transiciones está bien cubierto. Pocas transiciones prohibidas.","si_bajo":"Muchas transiciones no ocurren. Hay restricciones estructurales.","pregunta":"¿El espacio de transiciones está lleno o tiene restricciones?"},

    # === EJE 9: GEOMETRÍA DIFERENCIAL (5 features) ===
    "marco_curvatura_media": {"polos":("trayectoria recta","trayectoria sinuosa"),"eje":"curvatura media","presupuestos":["1 - cos(dir_i, dir_{i+1}) promediado","Mide cuánto gira la trayectoria en el espacio funcional"],"razonamiento":[("Calcular vectores de dirección entre segmentos","¿Hacia dónde va en cada tramo?","DIRECCIÓN"),("Medir ángulo entre direcciones consecutivas","¿Cuánto gira?","CURVATURA"),("Promediar","Media de giros","RESULTADO")],"si_alto":"El discurso gira mucho. Cambios de dirección frecuentes.","si_bajo":"El discurso va recto. Dirección consistente.","pregunta":"¿Cuánto gira la trayectoria del discurso?"},
    "marco_curvatura_max": {"polos":("sin giros bruscos","giro muy brusco"),"eje":"giro máximo","presupuestos":["Máxima curvatura puntual"],"razonamiento":[("Tomar la curvatura máxima","¿Cuál es el giro más brusco?","RESULTADO")],"si_alto":"Hay un giro MUY brusco. Posible contradicción o cambio radical.","si_bajo":"Ningún giro destaca. Transiciones suaves.","pregunta":"¿Hay algún giro brusco (contradicción, cambio radical)?"},
    "marco_torsion": {"polos":("ritmo constante","ritmo cambiante"),"eje":"cambio de curvatura","presupuestos":["Media de cambios absolutos en curvatura","Torsión = la curvatura misma cambia"],"razonamiento":[("Medir cómo cambia la curvatura entre tramos","¿El ritmo de giro es constante o variable?","RESULTADO")],"si_alto":"El ritmo de giro cambia. Trayectoria impredecible.","si_bajo":"El ritmo de giro es constante. Trayectoria predecible.","pregunta":"¿El ritmo de cambio de dirección es constante o variable?"},
    "marco_ratio_inflexion": {"polos":("sin puntos de inflexión","muchos puntos de inflexión"),"eje":"cambios de régimen","presupuestos":["Proporción de curvaturas > 1 (cos < 0 = giro de más de 90°)"],"razonamiento":[("Contar puntos donde cos < 0","¿Cuántos giros pasan de 90°?","PUNTOS de inflexión"),("Normalizar","Proporción","RESULTADO")],"si_alto":"Muchos cambios de régimen. El discurso zigzaguea.","si_bajo":"Pocos o ningún cambio de régimen. Discurso consistente.","pregunta":"¿Cuántos cambios de régimen (>90° de giro) hay?"},
    "marco_ratio_curv_if": {"polos":("más curvatura al final","más curvatura al inicio"),"eje":"distribución temporal de curvatura","presupuestos":["Curvatura inicio / curvatura fin"],"razonamiento":[("Comparar curvatura del primer tercio con el último","¿Gira más al principio o al final?","RESULTADO")],"si_alto":"Más giros al principio que al final. El discurso se estabiliza.","si_bajo":"Más giros al final. El discurso se desestabiliza.","pregunta":"¿El discurso gira más al principio o al final?"},

    # === EJE 10: CINEMÁTICA (6 features) ===
    "marco_vel_media": {"polos":("estático","rápido"),"eje":"velocidad media de cambio","presupuestos":["Distancia euclidiana entre centroides de segmentos consecutivos"],"razonamiento":[("Dividir secuencia en segmentos","¿Cómo evoluciona?","SEGMENTOS"),("Medir distancia entre centroides consecutivos","¿Cuánto se movió por segmento?","VELOCIDAD"),("Promediar","Media","RESULTADO")],"si_alto":"El discurso cambia rápido. Alta dinámica.","si_bajo":"El discurso cambia poco. Estabilidad o estancamiento.","pregunta":"¿A qué velocidad cambia la estructura del discurso?"},
    "marco_vel_max": {"polos":("sin cambios bruscos","cambio muy rápido"),"eje":"velocidad máxima","presupuestos":["Máxima distancia entre centroides consecutivos"],"razonamiento":[("Tomar la velocidad máxima","¿Cuál fue el cambio más rápido?","RESULTADO")],"si_alto":"Hubo un cambio MUY rápido en algún punto. Posible shock o giro de guion.","si_bajo":"Ningún cambio destaca por velocidad. Evolución gradual.","pregunta":"¿Hubo algún momento de cambio extremadamente rápido?"},
    "marco_aceleracion": {"polos":("frenando","acelerando"),"eje":"aceleración","presupuestos":["Media de cambios en velocidad","Positivo = se acelera, negativo = se frena"],"razonamiento":[("Calcular cambios en velocidad entre tramos","¿Se acelera o frena?","RESULTADO")],"si_alto":"El discurso se acelera. Tensión creciente o urgencia.","si_bajo":"El discurso se frena. Resolución o cierre.","pregunta":"¿La velocidad de cambio está aumentando o disminuyendo?"},
    "marco_bruscos": {"polos":("sin shocks","shocks frecuentes"),"eje":"frecuencia de shocks","presupuestos":["Proporción de velocidades > media + 2σ"],"razonamiento":[("Identificar velocidades anormalmente altas","¿Cuántos cambios son outliers?","RESULTADO")],"si_alto":"Cambios abruptos frecuentes. Giros de guion múltiples.","si_bajo":"Sin cambios abruptos. Evolución suave.","pregunta":"¿Con qué frecuencia hay cambios bruscos?"},
    "marco_coherencia_dir": {"polos":("zigzaguea","dirección consistente"),"eje":"coherencia direccional","presupuestos":["Media de cos(dir_i, dir_{i+1})","Mide si las direcciones consecutivas apuntan al mismo sitio"],"razonamiento":[("Calcular coseno entre direcciones consecutivas","¿Van hacia el mismo sitio?","CONCORDANCIA"),("Promediar","Media de concordancia","RESULTADO")],"si_alto":"El discurso va en una dirección consistente. Propósito claro.","si_bajo":"El discurso cambia de dirección constantemente. Sin propósito claro.","pregunta":"¿El discurso se mueve en una dirección consistente?"},
    "marco_desplazamiento": {"polos":("circular (vuelve al inicio)","transformación (acaba lejos)"),"eje":"desplazamiento total","presupuestos":["Distancia euclidiana entre centroide inicial y final"],"razonamiento":[("Medir distancia entre donde empezó y donde acabó","¿Terminó lejos de donde empezó?","RESULTADO")],"si_alto":"El texto termina MUY lejos de donde empezó. Hubo transformación.","si_bajo":"El texto vuelve a donde empezó. Circular o sin progreso.","pregunta":"¿El texto acaba lejos de donde empezó (transformación) o vuelve al inicio (circular)?"},
}

SEMANTICA.update(SEMANTICA_MARCOS)


def obtener_semantica(nombre_formula):
    """Devuelve la semántica completa de una fórmula."""
    return SEMANTICA.get(nombre_formula, None)


def razonamiento_a_texto(nombre_formula, valor=None):
    """Genera texto de razonamiento para el LLM.

    En vez de "varianza = 0.034", produce:
    "La dispersión es baja (concentrado).
     Esto significa: los puntos están cerca del centro, no hay extremos,
     el grupo es homogéneo, lo que le pasa al típico le pasa a casi todos."
    """
    sem = SEMANTICA.get(nombre_formula)
    if not sem:
        return None

    lines = []
    lines.append(f"**{nombre_formula}** — {sem['pregunta']}")
    lines.append(f"Eje: {sem['polos'][0]} ↔ {sem['polos'][1]}")

    if valor is not None:
        # Determinar polo
        from decodificador_economia import clasificar_nivel
        tipo = sem["eje"].replace(" ", "_").lower()
        ni, nt = clasificar_nivel(valor, tipo) if tipo else (2, "normal")
        lines.append(f"Valor: {valor:.4f} → {nt}")

        if ni >= 3:
            lines.append(f"Interpretación: {sem['si_alto']}")
        elif ni <= 1:
            lines.append(f"Interpretación: {sem['si_bajo']}")

    lines.append(f"\nProceso de razonamiento:")
    for paso, operacion, produce in sem["razonamiento"]:
        lines.append(f"  {paso}")
        lines.append(f"    → {operacion}")
        lines.append(f"    = {produce}")

    if sem.get("presupuestos"):
        lines.append(f"\n⚠️ Presupuestos (lo que asume sin decirlo):")
        for p in sem["presupuestos"]:
            lines.append(f"  - {p}")

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print(f"Fórmulas con semántica: {len(SEMANTICA)}")
    print()

    # Ejemplo: varianza
    texto = razonamiento_a_texto("varianza", 0.034)
    print(texto)
    print("\n" + "="*70 + "\n")

    # Ejemplo: correlación
    texto = razonamiento_a_texto("correlacion", -0.92)
    print(texto)
    print("\n" + "="*70 + "\n")

    # Ejemplo: output_gap
    texto = razonamiento_a_texto("output_gap", -0.07)
    print(texto)
    print("\n" + "="*70 + "\n")

    # Ejemplo: prospect_value
    texto = razonamiento_a_texto("prospect_value", -50)
    print(texto)
