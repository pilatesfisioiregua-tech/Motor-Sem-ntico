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
