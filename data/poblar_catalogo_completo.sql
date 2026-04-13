-- ============================================================

-- CATÁLOGO COMPLETO — generado automáticamente

-- Fecha: 2026-04-13

-- ============================================================



-- 294 fórmulas
-- 362 fórmulas con semántica
DELETE FROM catalogo_formulas;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('media', 'μ = Σxi / n', 'estadistica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','NORMALIZAR'], 'acumula todos los valores y normaliza por cantidad → dónde está el centro', 'sujeto (punto de referencia del conjunto)', 'bajo', 'alto', 'nivel central', ARRAY['Todos los valores pesan igual','Los extremos influyen (no es robusta a outliers)','Es el centro democrático, no el más frecuente'], '[{"paso": "Sumar todos los valores", "operacion": "Acumular en un eje", "produce": "ACUMULACIÓN: total del grupo"}, {"paso": "Dividir por n", "operacion": "Normalizar por cantidad", "produce": "RESULTADO: valor típico por elemento"}]'::jsonb, 'El nivel central del grupo está arriba. La mayoría tiene valores altos.', 'El nivel central está abajo. La mayoría tiene valores bajos.', '¿Dónde está el punto típico del grupo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('mediana', 'x_{n/2} de la serie ordenada', 'estadistica', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','SELECCIONAR'], 'transforma a serie ordenada y selecciona el punto central → centro robusto', 'sujeto robusto (centro que ignora extremos)', 'bajo', 'alto', 'centro robusto', ARRAY['Inmune a outliers (a diferencia de la media)','Ignora magnitud — solo mira posición'], '[{"paso": "Ordenar valores", "operacion": "Ranking", "produce": "secuencia"}, {"paso": "Tomar el del medio", "operacion": "Centro posicional", "produce": "RESULTADO: valor típico que ignora extremos"}]'::jsonb, 'El centro real del grupo está arriba.', 'El centro real está abajo.', '¿Cuál es el valor central ignorando extremos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('varianza', 'σ² = Σ(xi-μ)² / n', 'estadistica', ARRAY['DIAGNOSTICAR','MEDIR_RIESGO'], ARRAY['ACUMULAR','NORMALIZAR','COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR'], 'encuentra el centro (media), compara cada punto con el centro, transforma a magnitud (²), acumula magnitudes, normaliza por cantidad → cuánta dispersión por punto', 'adjetivo predicativo de dispersión', 'concentrado', 'disperso', 'dispersión', ARRAY['El centro es la media aritmética (todos pesan igual)','El cuadrado penaliza extremos desproporcionadamente','La dirección no importa (arriba y abajo pesan igual)','Cada observación pesa igual (no hay privilegiados)'], '[{"paso": "Sumar todos los valores y dividir por n", "operacion": "Encontrar el punto típico (media)", "produce": "SUJETO: el centro de referencia"}, {"paso": "Restar cada valor menos el centro", "operacion": "Medir cuánto se aleja cada punto", "produce": "ADJETIVO: distancia con dirección (+/-)"}, {"paso": "Elevar al cuadrado cada distancia", "operacion": "Eliminar dirección, amplificar extremos", "produce": "TRANSFORMACIÓN: de distancia a magnitud"}, {"paso": "Sumar todas las magnitudes", "operacion": "Acumular toda la diferencia del grupo", "produce": "ACUMULACIÓN: dispersión total"}, {"paso": "Dividir por n", "operacion": "Normalizar por cantidad", "produce": "RESULTADO: dispersión por elemento"}]'::jsonb, 'Los puntos están lejos del centro. Hay extremos. El grupo es heterogéneo. Lo que le pasa al típico NO le pasa a todos.', 'Los puntos están cerca del centro. No hay extremos. El grupo es homogéneo. Lo que le pasa al típico le pasa a casi todos.', '¿Cuán diferentes son los elementos entre sí?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('desviacion_estandar', 'σ = √(Σ(xi-μ)² / n)', 'estadistica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','NORMALIZAR','COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','TRANSFORMAR'], 'varianza + transforma de vuelta al eje original (√) → dispersión en unidades originales', 'adjetivo predicativo de dispersión en escala original', 'concentrado', 'disperso', 'dispersión en unidades originales', ARRAY['Mismos que varianza pero en escala original (raíz cuadrada devuelve al eje)','Más interpretable que varianza pero menos tratable matemáticamente'], '[{"paso": "Calcular varianza", "operacion": "dispersión al cuadrado", "produce": "magnitud cuadrada"}, {"paso": "Raíz cuadrada", "operacion": "volver al eje original", "produce": "RESULTADO: dispersión en las mismas unidades que los datos"}]'::jsonb, 'Los datos varían mucho alrededor del centro.', 'Los datos están agrupados cerca del centro.', '¿Cuánto varían los datos en sus propias unidades?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('coeficiente_variacion', 'CV = σ / μ', 'estadistica', ARRAY['DIAGNOSTICAR','MEDIR_RIESGO'], ARRAY['ACUMULAR','NORMALIZAR','COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','TRANSFORMAR','NORMALIZAR'], 'desviación estándar normalizada por la media → dispersión RELATIVA al nivel', 'adjetivo predicativo de dispersión relativa', 'predecible', 'impredecible', 'dispersión relativa', ARRAY['Normaliza por la media — comparable entre variables con diferentes escalas','Pierde sentido si la media es cercana a cero'], '[{"paso": "Calcular desviación estándar", "operacion": "dispersión absoluta", "produce": "cuánto varían"}, {"paso": "Dividir por la media", "operacion": "relativizar", "produce": "RESULTADO: cuánto varían RESPECTO a su nivel"}]'::jsonb, 'Variable impredecible — su variación es grande respecto a su nivel.', 'Variable predecible — su variación es pequeña respecto a su nivel.', '¿Cuán impredecible es esta variable respecto a su nivel?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('skewness', 'γ = E[(X-μ)³] / σ³', 'estadistica', ARRAY['DIAGNOSTICAR','MEDIR_RIESGO'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','NORMALIZAR'], 'compara con el centro, transforma al cubo (preserva dirección + amplifica extremos), acumula, normaliza 2x → hacia dónde se inclina', 'adjetivo de asimetría (dirección del riesgo)', 'cola izquierda (riesgo de caída)', 'cola derecha (potencial de subida)', 'asimetría', ARRAY['El cubo preserva dirección pero amplifica extremos 3x más que la varianza','Asume que la media es el centro relevante'], '[{"paso": "Restar cada valor menos la media", "operacion": "Distancia con signo", "produce": "POSICIÓN relativa al centro"}, {"paso": "Elevar al cubo", "operacion": "Preservar signo + amplificar extremos brutalmente", "produce": "TRANSFORMACIÓN: magnitud direccional extrema"}, {"paso": "Sumar y normalizar", "operacion": "¿Pesan más los extremos de arriba o los de abajo?", "produce": "RESULTADO: hacia dónde se inclina la distribución"}]'::jsonb, 'Hay cola derecha: potencial de resultados extremos positivos. La distribución se estira hacia arriba.', 'Hay cola izquierda: riesgo de caídas extremas. La distribución se estira hacia abajo.', '¿El riesgo está arriba o abajo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kurtosis', 'κ = E[(X-μ)⁴] / σ⁴', 'estadistica', ARRAY['DIAGNOSTICAR','MEDIR_RIESGO'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','NORMALIZAR'], 'como skewness pero a la 4ª potencia → amplifica extremos aún más → cuán probables son los eventos extremos', 'adjetivo de riesgo de colas', 'colas ligeras (sin extremos)', 'colas pesadas (extremos probables)', 'riesgo de eventos extremos', ARRAY['Cuarta potencia amplifica extremos brutalmente','Kurtosis=3 es ''normal'' (mesokúrtica)','No dice cuán grande será el extremo, solo cuán probable'], '[{"paso": "Elevar desviaciones a la cuarta potencia", "operacion": "Amplificar extremos exponencialmente", "produce": "Detectar colas"}, {"paso": "Normalizar", "operacion": "Comparar con distribución normal", "produce": "RESULTADO: cuán probable es un cisne negro"}]'::jsonb, 'Eventos extremos son más probables de lo que parece. Cuidado con los cisnes negros.', 'Eventos extremos son raros. La distribución es bien comportada.', '¿Cuán probables son los eventos extremos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('correlacion', 'ρ = Σ(xi-μx)(yi-μy) / (n·σx·σy)', 'estadistica', ARRAY['RELACIONAR'], ARRAY['COMPARAR','COMPARAR','COMPONER','ACUMULAR','NORMALIZAR','NORMALIZAR'], 'compara cada X con su centro, compara cada Y con su centro, compone las distancias (×), acumula, normaliza 2x → cuánto se mueven juntos', 'adjetivo de relación entre dos ejes', 'independientes', 'co-dependientes', 'relación lineal', ARRAY['Solo mide relación LINEAL (puede haber relación no lineal con corr=0)','Correlación ≠ causalidad (pueden moverse juntas por un tercero)','Es simétrica: corr(X,Y) = corr(Y,X) — no dice quién causa a quién','Sensible a outliers (un punto extremo puede crear o destruir correlación)'], '[{"paso": "Para cada X, medir distancia al centro de X", "operacion": "Cuánto se desvía X de su típico", "produce": "ADJETIVO de X: está por encima/debajo"}, {"paso": "Para cada Y, medir distancia al centro de Y", "operacion": "Cuánto se desvía Y de su típico", "produce": "ADJETIVO de Y: está por encima/debajo"}, {"paso": "Multiplicar ambas desviaciones", "operacion": "Cuando ambos están arriba: producto positivo. Uno arriba y otro abajo: negativo", "produce": "COMPOSICIÓN: ¿se desvían en la misma dirección?"}, {"paso": "Sumar todos los productos", "operacion": "Acumular la concordancia de dirección", "produce": "ACUMULACIÓN: co-movimiento total"}, {"paso": "Dividir por n×σx×σy", "operacion": "Normalizar para que esté entre -1 y +1", "produce": "RESULTADO: grado de co-movimiento normalizado"}]'::jsonb, 'Cuando X sube, Y sube (positiva) o baja (negativa). Se mueven JUNTAS. Lo que afecta a una afecta a la otra.', 'X e Y se mueven INDEPENDIENTEMENTE. Lo que afecta a una no dice nada sobre la otra.', '¿Se mueven juntas estas dos variables?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('covarianza', 'Cov = Σ(xi-μx)(yi-μy) / n', 'estadistica', ARRAY['RELACIONAR'], ARRAY['COMPARAR','COMPARAR','COMPONER','ACUMULAR','NORMALIZAR'], 'como correlación sin normalizar por desviaciones → co-movimiento en unidades originales', 'adjetivo de co-movimiento absoluto', 'bajo', 'alto', 'adjetivo de co-movimiento absoluto', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de co-movimiento absoluto.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de co-movimiento absoluto.', '¿co-movimiento en unidades originales?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('percentil', 'P_k = valor en posición k·n/100', 'estadistica', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ESCALAR','SELECCIONAR'], 'transforma a serie ordenada, escala posición, selecciona → dónde está este punto en la distribución', 'adjetivo de posición relativa', 'cola inferior', 'cola superior', 'posición en la distribución', ARRAY['No asume forma de distribución (no paramétrico)','Ordena todos los datos — sensible a la muestra'], '[{"paso": "Ordenar todos los valores", "operacion": "Crear ranking", "produce": "posición relativa"}, {"paso": "Seleccionar el valor en la posición k%", "operacion": "Encontrar umbral", "produce": "RESULTADO: qué valor deja k% debajo"}]'::jsonb, 'Este valor está en la cola superior — mejor que la mayoría.', 'Este valor está en la cola inferior — peor que la mayoría.', '¿Dónde está este valor en la distribución?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gini', 'G = (2·Σi·xi) / (n·Σxi) - (n+1)/n', 'estadistica', ARRAY['DIAGNOSTICAR','COMPARAR'], ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR','NORMALIZAR','COMPARAR'], 'ordena, pondera por posición, acumula, normaliza, compara con distribución uniforme → cuánta desigualdad', 'adjetivo de concentración/desigualdad', 'igualdad perfecta', 'un individuo tiene todo', 'desigualdad', ARRAY['Compara TODOS los pares (no solo rico vs pobre)','No distingue desigualdad arriba vs abajo (Gini=0.4 puede ser pocos ricos o muchos pobres)','Es relativa: no cambia si todos duplican su renta'], '[{"paso": "Ordenar todos los valores de menor a mayor", "operacion": "Ver la distribución acumulada", "produce": "ESTRUCTURA: curva de Lorenz"}, {"paso": "Ponderar cada valor por su posición en la fila", "operacion": "Los últimos (más ricos) pesan más por su posición", "produce": "PONDERACIÓN posicional"}, {"paso": "Normalizar y comparar con igualdad perfecta", "operacion": "¿Cuán lejos estamos de que todos tengan igual?", "produce": "RESULTADO: distancia a la igualdad"}]'::jsonb, 'Pocos tienen mucho, muchos tienen poco. Desigualdad severa. La riqueza se concentra.', 'La distribución es equilibrada. Todos tienen cantidades similares.', '¿Cuánta desigualdad hay en la distribución?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('entropia_shannon', 'H = -Σp·log(p)', 'estadistica', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','COMPONER','ACUMULAR','TRANSFORMAR'], 'normaliza a probabilidades, transforma a log (comprime), compone p×log(p), acumula, invierte signo → cuánta incertidumbre/diversidad', 'adjetivo de diversidad/incertidumbre', 'certeza total (un solo tipo)', 'incertidumbre máxima (todos los tipos igual)', 'diversidad/incertidumbre', ARRAY['Usa logaritmo: añadir un tipo nuevo pesa menos cuantos más hay','Todos los tipos son igualmente valiosos (no hay jerarquía)','Mide diversidad de tipos, no de cantidades'], '[{"paso": "Normalizar a proporciones (frecuencias relativas)", "operacion": "¿Qué fracción es cada tipo?", "produce": "DISTRIBUCIÓN de probabilidad"}, {"paso": "Tomar logaritmo de cada proporción", "operacion": "Comprimir: lo frecuente pesa poco, lo raro pesa mucho", "produce": "TRANSFORMACIÓN: sorpresa por tipo"}, {"paso": "Multiplicar proporción × log(proporción)", "operacion": "Ponderar la sorpresa por cuán frecuente es", "produce": "COMPOSICIÓN: sorpresa esperada por tipo"}, {"paso": "Sumar e invertir signo", "operacion": "Acumular sorpresa total", "produce": "RESULTADO: incertidumbre total del sistema"}]'::jsonb, 'Muchos tipos diferentes, ninguno domina. Alta diversidad. Si eliges uno al azar, no sabes cuál será.', 'Pocos tipos o uno domina. Baja diversidad. Si eliges al azar, ya sabes qué va a salir.', '¿Cuánta sorpresa hay en el sistema?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('utilidad_marginal', 'MU = ∂U/∂x', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR'], 'deriva la utilidad respecto al bien → cuánta satisfacción adicional por unidad', 'adjetivo de satisfacción marginal', 'bajo', 'alto', 'adjetivo de satisfacción marginal', ARRAY['Asume diferenciabilidad — la función es suave','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de satisfacción marginal.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de satisfacción marginal.', '¿cuánta satisfacción adicional por unidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tasa_marginal_sustitucion', 'TMS = MUx/MUy = -dy/dx|U=cte', 'micro', ARRAY['RELACIONAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR'], 'deriva utilidad por X, deriva por Y, divide → cuánto Y sacrificas por 1 más de X', 'adjetivo de sustituibilidad', 'complementarios (no sustituyes)', 'sustitutos (intercambias fácilmente)', 'sustituibilidad', ARRAY['Mide sobre curva de indiferencia (utilidad constante)','Es local — puede cambiar en otros puntos'], '[{"paso": "Medir utilidad marginal de X y de Y", "operacion": "¿Cuánto valoras cada uno?", "produce": "Valoraciones"}, {"paso": "Dividir UMx/UMy", "operacion": "Ratio de valoraciones", "produce": "RESULTADO: cuántas unidades de Y sacrificas por 1 más de X"}]'::jsonb, 'X vale mucho más que Y para ti. Sacrificas mucho Y por poco X.', 'X y Y valen similar. No sacrificas mucho de uno por el otro.', '¿Cuánto de Y estás dispuesto a dar por una unidad más de X?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('elasticidad_precio', 'ε = (∂Q/Q)/(∂P/P) = (∂Q/∂P)·(P/Q)', 'micro', ARRAY['RELACIONAR'], ARRAY['DERIVAR','NORMALIZAR','DERIVAR','NORMALIZAR','NORMALIZAR'], 'deriva cantidad respecto a precio, normaliza ambos por sus niveles → cambio proporcional de demanda por cambio proporcional de precio', 'adjetivo de sensibilidad proporcional', 'inelástico (insensible)', 'elástico (hipersensible)', 'sensibilidad proporcional', ARRAY['Mide cambios PROPORCIONALES, no absolutos','Asume que la relación es local (cerca del punto actual)','Es caeteris paribus: todo lo demás constante'], '[{"paso": "Medir cambio porcentual en cantidad cuando precio cambia 1%", "operacion": "¿Cuánto reacciona la demanda?", "produce": "SENSIBILIDAD: reacción proporcional"}, {"paso": "Si |ε|<1: inelástico", "operacion": "La demanda reacciona menos que proporcional", "produce": "CONCLUSIÓN: subir precio SUBE ingresos"}, {"paso": "Si |ε|>1: elástico", "operacion": "La demanda reacciona más que proporcional", "produce": "CONCLUSIÓN: subir precio BAJA ingresos"}, {"paso": "Si |ε|=1: unitario", "operacion": "La demanda reacciona exactamente proporcional", "produce": "CONCLUSIÓN: ingresos no cambian"}]'::jsonb, 'Los consumidores son MUY sensibles al precio. Subir precio = perder clientes rápido. Competencia alta o muchos sustitutos.', 'Los consumidores son INSENSIBLES al precio. Subir precio = mantener clientes. Necesidad, adicción, o sin sustitutos.', '¿Cuánto reacciona la demanda a un cambio de precio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('excedente_consumidor', 'EC = ∫[0,Q*] D(q)dq - P*·Q*', 'micro', ARRAY['VALORAR'], ARRAY['INTEGRAR','COMPONER','COMPARAR'], 'integra la curva de demanda (lo que estaría dispuesto a pagar), compone precio×cantidad (lo que paga), compara → beneficio neto del consumidor', 'adjetivo de bienestar del consumidor', 'sin beneficio (paga lo que valora)', 'gran beneficio (paga mucho menos de lo que valora)', 'bienestar del consumidor', ARRAY['Asume que la curva de demanda revela la valoración real','Usa integral: suma continua de valoraciones marginales','Es una aproximación (exacta solo con utilidad cuasilineal)'], '[{"paso": "Para cada unidad, calcular cuánto estaría dispuesto a pagar", "operacion": "Valoración marginal decreciente", "produce": "CURVA de demanda = curva de valoración"}, {"paso": "Integrar todas las valoraciones desde 0 hasta Q*", "operacion": "Sumar cuánto VALORARÍA pagar en total", "produce": "ACUMULACIÓN: valor total percibido"}, {"paso": "Restar precio×cantidad (lo que realmente paga)", "operacion": "Comparar valoración con gasto real", "produce": "COMPARACIÓN: valor - coste"}, {"paso": "La diferencia es el excedente", "operacion": "Lo que gana por pagar menos de lo que valora", "produce": "RESULTADO: beneficio neto del consumidor"}]'::jsonb, 'El consumidor obtiene mucho valor por poco dinero. Está mucho mejor con el intercambio que sin él.', 'El consumidor paga casi lo que valora. El intercambio apenas le beneficia. Poder de mercado del vendedor.', '¿Cuánto gana el consumidor por participar en este mercado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('coste_marginal', 'MC = dC/dq', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR'], 'deriva el coste total respecto a la cantidad → cuánto cuesta producir una unidad más', 'adjetivo de coste incremental', 'bajo', 'alto', 'adjetivo de coste incremental', ARRAY['Asume diferenciabilidad — la función es suave','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de coste incremental.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de coste incremental.', '¿cuánto cuesta producir una unidad más?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('beneficio_maximo', 'π* : dπ/dq = 0 → MR = MC', 'micro', ARRAY['OPTIMIZAR'], ARRAY['DERIVAR','COMPARAR','SELECCIONAR'], 'deriva beneficio, compara ingreso marginal con coste marginal, selecciona punto donde son iguales → producción óptima', 'sujeto (punto óptimo de producción)', 'bajo valor', 'alto valor', 'sujeto (punto óptimo de producción)', ARRAY['Asume que el óptimo existe y es alcanzable','Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (punto óptimo de producción).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿producción óptima?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('indice_lerner', 'L = (P-MC)/P', 'micro', ARRAY['COMPARAR'], ARRAY['COMPARAR','NORMALIZAR'], 'compara precio con coste marginal, normaliza por precio → cuánto poder de mercado tiene la empresa', 'adjetivo de poder de mercado', 'competencia perfecta (cero poder)', 'monopolio puro (máximo poder)', 'poder de mercado', ARRAY['Asume que el precio y el coste marginal son observables','Ignora poder de mercado dinámico (puede tener precio bajo hoy para capturar mañana)','Isomorfo con tasa de crecimiento, output gap y Sharpe (COMPARAR→NORMALIZAR)'], '[{"paso": "Medir precio de venta", "operacion": "¿Cuánto cobra?", "produce": "NIVEL del precio"}, {"paso": "Medir coste marginal", "operacion": "¿Cuánto le cuesta producir una unidad más?", "produce": "NIVEL del coste"}, {"paso": "Restar coste del precio", "operacion": "¿Cuánto markup hay?", "produce": "COMPARACIÓN: distancia precio-coste"}, {"paso": "Dividir por el precio", "operacion": "Normalizar por el nivel", "produce": "RESULTADO: markup como proporción del precio"}]'::jsonb, 'La empresa cobra mucho más de lo que cuesta producir. Tiene poder para fijar precio. Poca competencia.', 'La empresa cobra casi lo que cuesta producir. No tiene poder. Mucha competencia le obliga.', '¿Cuánto puede la empresa subir el precio sobre su coste?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hhi', 'HHI = Σsi²', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','ACUMULAR'], 'normaliza a cuotas de mercado, transforma al cuadrado (amplifica dominantes), acumula → cuán concentrado está el mercado', 'adjetivo de concentración de mercado', 'fragmentado (muchos pequeños)', 'concentrado (pocos grandes)', 'concentración de mercado', ARRAY['Solo mira cuotas, no barreras ni comportamiento','Cuadrado amplifica a los grandes'], '[{"paso": "Calcular cuota de mercado de cada empresa", "operacion": "¿Qué % tiene cada una?", "produce": "Participaciones"}, {"paso": "Elevar al cuadrado cada cuota", "operacion": "Amplificar a los grandes, minimizar a los pequeños", "produce": "PONDERACIÓN"}, {"paso": "Sumar", "operacion": "Índice de concentración", "produce": "RESULTADO: cuán dominado está el mercado"}]'::jsonb, 'Pocas empresas dominan. Riesgo de colusión y precios altos.', 'Muchas empresas pequeñas. Competencia intensa.', '¿Cuántas empresas dominan este mercado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equilibrio_nash', 'σ* : ui(σi*, σ-i*) ≥ ui(σi, σ-i*) ∀i,σi', 'micro', ARRAY['PRESCRIBIR'], ARRAY['COMPARAR','CONDICIONAR','SELECCIONAR'], 'compara payoff de cada estrategia condicionado a lo que hacen los demás, selecciona donde nadie mejora cambiando → punto de equilibrio', 'sujeto (estado de equilibrio estratégico)', 'inestable (incentivo a desviarse)', 'estable (nadie mejora cambiando)', 'estabilidad estratégica', ARRAY['Cada jugador es racional y conoce las estrategias del otro','Puede haber múltiples equilibrios','No necesariamente es el mejor resultado posible'], '[{"paso": "Para cada jugador, calcular mejor respuesta dado lo que hacen los demás", "operacion": "¿Qué harías si los demás no cambian?", "produce": "Mejor respuesta"}, {"paso": "Encontrar punto donde todas las mejores respuestas son consistentes", "operacion": "Nadie quiere cambiar", "produce": "RESULTADO: equilibrio — estado estable del conflicto"}]'::jsonb, 'El equilibrio es fuerte: desviarse cuesta mucho. Situación difícil de cambiar.', 'El equilibrio es débil: un pequeño cambio puede romperlo.', '¿Hay una situación donde nadie quiere cambiar su estrategia?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('valor_shapley', 'φi = Σ [|S|!(n-|S|-1)!/n!] · [v(S∪{i})-v(S)]', 'micro', ARRAY['DESCOMPONER'], ARRAY['COMPARAR','ESCALAR','ACUMULAR','NORMALIZAR'], 'compara valor con y sin el jugador i, escala por factor combinatorio, acumula sobre todas las coaliciones, normaliza → contribución justa de cada jugador', 'adjetivo de contribución justa', 'no contribuye', 'contribuye mucho', 'contribución justa', ARRAY['Mide contribución marginal MEDIA sobre todas las coaliciones posibles','Es el único valor que cumple eficiencia+simetría+nulidad+aditividad'], '[{"paso": "Para cada coalición posible, medir valor con y sin el jugador", "operacion": "¿Cuánto añade?", "produce": "Contribución marginal"}, {"paso": "Promediar sobre todas las coaliciones ponderado por combinatoria", "operacion": "Promediar el orden de llegada", "produce": "RESULTADO: contribución justa"}]'::jsonb, 'Este jugador aporta mucho. Sin él, el grupo vale significativamente menos.', 'Este jugador es prescindible. El grupo funciona similar sin él.', '¿Cuánto contribuye justamente cada jugador al resultado del grupo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('deadweight_loss', 'DWL = ½·(P_m-P_c)·(Q_c-Q_m)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPARAR','COMPONER','ESCALAR'], 'compara precio monopolio vs competitivo, compara cantidades, compone ambas diferencias (área del triángulo), escala por ½ → pérdida que no recupera nadie', 'adjetivo de ineficiencia social', 'sin pérdida (mercado eficiente)', 'pérdida masiva (distorsión severa)', 'ineficiencia social', ARRAY['Compara con el óptimo de competencia perfecta','Asume que la curva de demanda refleja beneficio social y la de oferta refleja coste social','Ignora externalidades (si las hay, el ''óptimo'' puede ser otro)'], '[{"paso": "Comparar precio de mercado con precio competitivo", "operacion": "¿Cuánto distorsiona el precio?", "produce": "DISTORSIÓN en precio"}, {"paso": "Comparar cantidad de mercado con cantidad competitiva", "operacion": "¿Cuánto se deja de producir?", "produce": "DISTORSIÓN en cantidad"}, {"paso": "Multiplicar ambas diferencias × ½ (triángulo)", "operacion": "Área que nadie captura: ni productor, ni consumidor, ni gobierno", "produce": "RESULTADO: bienestar destruido"}]'::jsonb, 'Mucho bienestar se destruye. Transacciones que beneficiarían a ambas partes no ocurren. La economía funciona mal.', 'Poco bienestar perdido. El mercado funciona cerca del óptimo. La distorsión es pequeña.', '¿Cuánto bienestar se destruye por la distorsión del mercado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('pib', 'Y = C + I + G + (X-M)', 'macro', ARRAY['DIAGNOSTICAR','DESCOMPONER'], ARRAY['ACUMULAR','COMPARAR','ACUMULAR'], 'acumula consumo+inversión+gasto, compara exportaciones-importaciones, acumula todo → producción total', 'sujeto (tamaño de la economía)', 'bajo valor', 'alto valor', 'sujeto (tamaño de la economía)', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (tamaño de la economía).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿producción total?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('deflactor', 'D = PIB_nominal / PIB_real × 100', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','ESCALAR'], 'normaliza nominal por real, escala a índice → cuánto subieron los precios en general', 'adjetivo de nivel de precios', 'bajo', 'alto', 'adjetivo de nivel de precios', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de nivel de precios.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de nivel de precios.', '¿cuánto subieron los precios en general?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tasa_crecimiento', 'g = (Yt - Yt-1) / Yt-1', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR'], 'compara con el periodo anterior, normaliza por el nivel anterior → velocidad de crecimiento', 'adjetivo de velocidad', 'contracción', 'expansión', 'velocidad de la economía', ARRAY['Isomorfa con Lerner, output gap, Sharpe (COMPARAR→NORMALIZAR)','Solo mide velocidad, no dirección ni sostenibilidad'], '[{"paso": "Restar valor actual menos anterior", "operacion": "¿Cuánto cambió?", "produce": "CAMBIO absoluto"}, {"paso": "Dividir por valor anterior", "operacion": "Normalizar por el nivel", "produce": "RESULTADO: cambio proporcional"}]'::jsonb, 'La economía crece rápido. Puede ser sano o burbuja — depende de qué crece.', 'La economía se contrae. Puede ser recesión o ajuste necesario.', '¿A qué velocidad crece o decrece?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('solow_steady_state', 'k* : sf(k*) = (n+δ)k*', 'macro', ARRAY['DIAGNOSTICAR','OPTIMIZAR'], ARRAY['COMPONER','COMPONER','COMPARAR','SELECCIONAR'], 'compone ahorro×producción, compone depreciación×capital, compara inversión con depreciación, selecciona donde son iguales → capital de largo plazo', 'sujeto (estado estacionario)', 'subdesarrollado (lejos del estado estacionario)', 'desarrollado (en estado estacionario)', 'posición de largo plazo', ARRAY['Rendimientos decrecientes del capital','Ahorro exógeno y constante','Sin progreso técnico en versión básica'], '[{"paso": "Calcular inversión: s×f(k)", "operacion": "¿Cuánto capital nuevo se crea?", "produce": "INVERSIÓN"}, {"paso": "Calcular depreciación: (n+δ)×k", "operacion": "¿Cuánto capital se destruye?", "produce": "DEPRECIACIÓN"}, {"paso": "Encontrar k* donde inversión = depreciación", "operacion": "Equilibrio de largo plazo", "produce": "RESULTADO: nivel de capital sostenible"}]'::jsonb, 'Alto capital por trabajador = economía rica. Pero crecimiento se frena (rendimientos decrecientes).', 'Bajo capital = economía pobre pero con potencial de crecimiento rápido (convergencia).', '¿Cuál es el nivel de riqueza de largo plazo de esta economía?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('residuo_solow', 'A = Y / (K^α · L^(1-α))', 'macro', ARRAY['DESCOMPONER'], ARRAY['TRANSFORMAR','COMPONER','NORMALIZAR'], 'transforma inputs por elasticidades, compone capital×trabajo, normaliza output por inputs → lo que no explican los factores (productividad)', 'residuo (lo no explicado = innovación)', 'sin innovación (todo se explica por capital+trabajo)', 'alta innovación (la productividad crece sola)', 'progreso tecnológico', ARRAY['''La medida de nuestra ignorancia'' (Solow)','Recoge TODO lo que no es capital ni trabajo (instituciones, educación, tecnología, errores de medición)'], '[{"paso": "Medir crecimiento del PIB", "operacion": "¿Cuánto creció?", "produce": "TOTAL"}, {"paso": "Restar contribución de capital (α×ΔK/K) y trabajo ((1-α)×ΔL/L)", "operacion": "¿Cuánto explican los factores?", "produce": "FACTORES"}, {"paso": "Lo que sobra es el residuo", "operacion": "Lo que no se explica", "produce": "RESULTADO: productividad total de los factores"}]'::jsonb, 'La economía crece por innovación, no por acumular más. Crecimiento sano y sostenible.', 'El crecimiento viene solo de más capital o más trabajadores. Insostenible sin innovación.', '¿Cuánto del crecimiento viene de la innovación vs acumulación bruta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ecuacion_euler', 'u''(ct) = β(1+r)u''(ct+1)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','ESCALAR','COMPARAR'], 'deriva utilidad hoy, deriva utilidad mañana, escala por descuento×retorno, compara → cuánto sacrificas hoy por mañana', 'adjetivo de paciencia intertemporal', 'bajo', 'alto', 'adjetivo de paciencia intertemporal', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de paciencia intertemporal.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de paciencia intertemporal.', '¿cuánto sacrificas hoy por mañana?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('curva_phillips', 'π = πe + β(Y-Y*) + ε', 'macro', ARRAY['RELACIONAR'], ARRAY['COMPARAR','ESCALAR','ACUMULAR'], 'compara output con potencial (gap), escala por sensibilidad, acumula expectativas + shock → inflación', 'adjetivo de presión inflacionaria', 'deflación/desempleo alto', 'inflación/pleno empleo', 'trade-off inflación-empleo', ARRAY['Asume relación estable entre inflación y desempleo — puede no serlo (estanflación)','Isomorfo con CAPM (COMPARAR→ESCALAR→ACUMULAR)','Versión moderna incluye expectativas — si la gente espera inflación, la relación cambia'], '[{"paso": "Medir output gap (o desempleo vs NAIRU)", "operacion": "¿Cuánta presión hay en el mercado laboral?", "produce": "PRESIÓN de demanda"}, {"paso": "Escalar por sensibilidad (κ)", "operacion": "¿Cuánta inflación genera cada punto de gap?", "produce": "TRANSMISIÓN: de actividad a precios"}, {"paso": "Sumar expectativas de inflación", "operacion": "Lo que la gente ESPERA que pase se autocumple", "produce": "COMPONENTE inercial"}, {"paso": "Resultado: inflación", "operacion": "Inflación = expectativas + presión de demanda", "produce": "RESULTADO: por qué suben los precios"}]'::jsonb, 'Economía caliente: mucha demanda, poco desempleo, precios subiendo. Típico final de expansión.', 'Economía fría: poca demanda, mucho desempleo, precios estables o cayendo. Típico recesión.', '¿Cuánta inflación genera la presión de la demanda?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regla_taylor', 'i = r* + π + 0.5(π-π*) + 0.5(Y-Y*)/Y*', 'macro', ARRAY['PRESCRIBIR','OPTIMIZAR'], ARRAY['COMPARAR','COMPARAR','ESCALAR','ESCALAR','ACUMULAR'], 'compara inflación con target, compara output con potencial, escala ambas desviaciones, acumula con tasa natural → tipo de interés óptimo', 'prescripción (qué debería hacer el banco central)', 'tipos bajos (estímulo)', 'tipos altos (restricción)', 'postura monetaria', ARRAY['Asume que el banco central puede y debe seguir una regla','Asume pesos iguales (0.5) a inflación y output gap — juicio de valor','Requiere conocer la tasa natural (r*) y el PIB potencial — ambos no observables'], '[{"paso": "Medir inflación actual vs objetivo", "operacion": "¿Cuánto se desvía la inflación?", "produce": "DESVIACIÓN inflacionaria"}, {"paso": "Medir output gap", "operacion": "¿Está la economía caliente o fría?", "produce": "DESVIACIÓN de actividad"}, {"paso": "Ponderar ambas desviaciones por 0.5", "operacion": "Dar peso igual a ambas preocupaciones", "produce": "PONDERACIÓN: estabilidad de precios vs empleo"}, {"paso": "Sumar con tasa natural + inflación actual", "operacion": "Construir la prescripción", "produce": "RESULTADO: tipo de interés que debería fijar el banco central"}]'::jsonb, 'El banco central debería restringir. Inflación alta y/o economía sobrecalentada.', 'El banco central debería estimular. Inflación baja y/o economía fría.', '¿A qué tipo de interés debería estar el banco central?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('multiplicador_fiscal', 'm = 1/(1-c(1-t))', 'macro', ARRAY['PRESCRIBIR'], ARRAY['COMPONER','COMPARAR','INVERTIR'], 'compone propensión marginal×(1-impuesto), compara con 1, invierte → cuánto se amplifica cada euro de gasto', 'adjetivo de amplificación', 'ineficaz (multiplicador < 1)', 'amplificador (multiplicador > 1)', 'potencia fiscal', ARRAY['Asume propensión marginal a consumir constante','Ignora efectos de crowding out (el gasto público desplaza inversión privada)','Asume economía cerrada (en economía abierta, parte se va en importaciones)','No distingue tipo de gasto (infraestructura vs transferencias)'], '[{"paso": "El gobierno gasta 1€ adicional", "operacion": "Un agente recibe 1€ más", "produce": "IMPULSO inicial"}, {"paso": "Ese agente consume c×1€ (c = propensión a consumir)", "operacion": "Parte del € se gasta, parte se ahorra", "produce": "PRIMERA RONDA: el € circula parcialmente"}, {"paso": "El siguiente agente recibe c€ y consume c²€", "operacion": "El € sigue circulando, cada vez más pequeño", "produce": "RONDAS SUCESIVAS: serie geométrica decreciente"}, {"paso": "Sumar todas las rondas: 1/(1-c)", "operacion": "Total acumulado de actividad generada", "produce": "RESULTADO: cuántos € de PIB genera cada € de gasto"}]'::jsonb, 'Cada euro de gasto público genera más de un euro de PIB. La economía amplifica el impulso. Política fiscal potente.', 'Cada euro genera menos de un euro. El dinero se filtra (ahorro, impuestos, importaciones). Política fiscal débil.', '¿Cuánto PIB genera cada euro de gasto público?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ecuacion_fisher', 'r = i - πe', 'macro', ARRAY['RELACIONAR'], ARRAY['COMPARAR'], 'compara tipo nominal con inflación esperada → tipo de interés real', 'adjetivo de coste real del dinero', 'tipo real negativo (la inflación se come los intereses)', 'tipo real positivo (los intereses superan la inflación)', 'coste real del dinero', ARRAY['Solo una resta — la fórmula más simple y más importante de la macro','Isomorfa con Modigliani-Miller, Bertrand, dominancia estocástica (COMPARAR)'], '[{"paso": "Tomar tipo de interés nominal", "operacion": "¿Cuánto te paga el banco?", "produce": "NOMINAL"}, {"paso": "Restar inflación esperada", "operacion": "¿Cuánto te quita la inflación?", "produce": "INFLACIÓN"}, {"paso": "La diferencia es el tipo real", "operacion": "¿Cuánto ganas de verdad?", "produce": "RESULTADO: el precio real del dinero"}]'::jsonb, 'El dinero tiene valor real positivo. Ahorrar compensa. Política monetaria restrictiva.', 'La inflación se come los intereses. Ahorrar es perder. Incentivo a gastar/invertir/especular.', '¿Cuál es el coste real de pedir prestado (o el retorno real de ahorrar)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('velocidad_dinero', 'V = PY/M', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','NORMALIZAR'], 'compone precios×output, normaliza por masa monetaria → cuántas veces circula cada euro', 'adjetivo de velocidad monetaria', 'bajo', 'alto', 'adjetivo de velocidad monetaria', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de velocidad monetaria.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de velocidad monetaria.', '¿cuántas veces circula cada euro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('output_gap', 'gap = (Y - Y*) / Y*', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR'], 'compara PIB real con potencial, normaliza → cuánto está la economía por encima/debajo de su capacidad', 'adjetivo de presión (inflacionaria si +, recesiva si -)', 'recesión (bajo potencial)', 'sobrecalentamiento (sobre potencial)', 'presión cíclica', ARRAY['Asume que el PIB potencial es observable (no lo es — se estima)','Isomorfo con Lerner, tasa de crecimiento y Sharpe (COMPARAR→NORMALIZAR)','Simétrico: desviaciones arriba y abajo se tratan igual'], '[{"paso": "Medir PIB real actual", "operacion": "¿Dónde estamos?", "produce": "NIVEL actual"}, {"paso": "Estimar PIB potencial", "operacion": "¿Dónde deberíamos estar?", "produce": "REFERENCIA: capacidad de la economía"}, {"paso": "Restar real menos potencial", "operacion": "¿Estamos por encima o por debajo?", "produce": "COMPARACIÓN: distancia al potencial"}, {"paso": "Dividir por potencial", "operacion": "Normalizar", "produce": "RESULTADO: desviación proporcional"}]'::jsonb, 'La economía produce MÁS de lo que puede sostener. Presión inflacionaria. Mercado laboral tensionado. Necesita enfriarse.', 'La economía produce MENOS de lo que puede. Capacidad ociosa. Desempleo. Necesita estímulo.', '¿La economía está por encima o por debajo de su capacidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ley_okun', 'Δu = -β·(ΔY/Y - g*)', 'macro', ARRAY['RELACIONAR'], ARRAY['DERIVAR','NORMALIZAR','COMPARAR','ESCALAR','TRANSFORMAR'], 'deriva crecimiento, normaliza, compara con crecimiento potencial, escala por sensibilidad, invierte signo → cuánto desempleo genera cada punto de gap', 'adjetivo de coste humano del gap', 'bajo', 'alto', 'adjetivo de coste humano del gap', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de coste humano del gap.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de coste humano del gap.', '¿cuánto desempleo genera cada punto de gap?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('capm', 'E[ri] = rf + βi·(E[rm]-rf)', 'finanzas', ARRAY['PRESCRIBIR','VALORAR'], ARRAY['COMPARAR','ESCALAR','ACUMULAR'], 'compara retorno mercado con tasa libre (prima), escala por beta (sensibilidad), acumula con tasa libre → retorno justo por el riesgo', 'prescripción (cuánto deberías ganar dado tu riesgo)', 'retorno bajo (activo seguro)', 'retorno alto (activo arriesgado)', 'retorno justo por riesgo', ARRAY['Solo el riesgo SISTEMÁTICO (de mercado) se compensa — el específico se diversifica','Asume mercados eficientes y agentes racionales','Isomorfo con Phillips (COMPARAR→ESCALAR→ACUMULAR)','Beta mide sensibilidad al mercado, no riesgo total'], '[{"paso": "Medir retorno del mercado menos tasa libre de riesgo", "operacion": "¿Cuánto paga el mercado por arriesgar?", "produce": "PRIMA de mercado"}, {"paso": "Multiplicar por beta del activo", "operacion": "¿Cuánto de ese riesgo tiene este activo?", "produce": "ESCALAR: exposición individual al riesgo"}, {"paso": "Sumar tasa libre de riesgo", "operacion": "Añadir la base de retorno sin riesgo", "produce": "RESULTADO: retorno que DEBERÍA tener el activo"}]'::jsonb, 'El activo debería rendir mucho porque tiene mucho riesgo sistemático. Si rinde menos, está sobrevalorado.', 'El activo debería rendir poco porque tiene poco riesgo. Si rinde más, es una ganga.', '¿Cuánto debería rendir este activo dado su riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('beta_capm', 'β = Cov(ri,rm) / Var(rm)', 'finanzas', ARRAY['RELACIONAR'], ARRAY['COMPARAR','COMPARAR','COMPONER','ACUMULAR','NORMALIZAR','COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','NORMALIZAR'], 'covarianza del activo con el mercado normalizada por varianza del mercado → cuánto se mueve el activo por cada 1% del mercado', 'adjetivo de sensibilidad al mercado', 'defensivo (β<1)', 'agresivo (β>1)', 'sensibilidad al mercado', ARRAY['Solo mide riesgo SISTEMÁTICO','Asume relación lineal y estable con el mercado'], '[{"paso": "Calcular covarianza del activo con el mercado", "operacion": "¿Se mueven juntos?", "produce": "CO-MOVIMIENTO"}, {"paso": "Dividir por varianza del mercado", "operacion": "Normalizar", "produce": "RESULTADO: cuánto se mueve el activo por cada 1% del mercado"}]'::jsonb, 'Activo agresivo: amplifica los movimientos del mercado. Sube más cuando todo sube, cae más cuando todo cae.', 'Activo defensivo: amortigua los movimientos del mercado.', '¿Cuánto amplifica o amortigua este activo los movimientos del mercado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('sharpe', 'S = (E[r]-rf) / σ', 'finanzas', ARRAY['COMPARAR'], ARRAY['COMPARAR','NORMALIZAR'], 'compara retorno con tasa libre, normaliza por volatilidad → cuánto ganas por cada unidad de riesgo', 'adjetivo de eficiencia riesgo/retorno', 'mal compensado (poco retorno por mucho riesgo)', 'bien compensado (mucho retorno por poco riesgo)', 'eficiencia riesgo-retorno', ARRAY['Usa desviación estándar como medida de riesgo (asume normalidad)','Isomorfo con Lerner, crecimiento, output gap (COMPARAR→NORMALIZAR)','No distingue volatilidad alcista de bajista (ambas son ''riesgo'')'], '[{"paso": "Medir retorno del activo menos tasa libre de riesgo", "operacion": "¿Cuánto exceso de retorno hay?", "produce": "PREMIO por arriesgar"}, {"paso": "Dividir por volatilidad (desviación estándar)", "operacion": "Normalizar por cuánto riesgo asumes", "produce": "RESULTADO: premio por unidad de riesgo"}]'::jsonb, 'Estás bien pagado por el riesgo que tomas. Inversión eficiente.', 'Estás mal pagado. Podrías obtener el mismo retorno con menos riesgo (o más retorno con el mismo riesgo).', '¿Estás bien compensado por el riesgo que asumes?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('valor_presente_neto', 'VPN = Σ CFt/(1+r)^t', 'finanzas', ARRAY['VALORAR'], ARRAY['ESCALAR','INVERTIR','TRANSFORMAR','ACUMULAR'], 'escala cada flujo por factor de descuento (invierte + transforma por exponente temporal), acumula → valor hoy de todos los flujos futuros', 'sujeto (valor fundamental del activo)', 'destruye valor (VPN < 0)', 'crea valor (VPN > 0)', 'creación de valor', ARRAY['La tasa de descuento refleja el coste de oportunidad — pero ¿cuál es?','Asume que los flujos futuros son conocidos (en realidad son estimaciones)','Un € hoy vale más que un € mañana — ¿cuánto más? Depende de r'], '[{"paso": "Para cada flujo futuro, dividir por (1+r)^t", "operacion": "¿Cuánto vale hoy lo que recibirás en t períodos?", "produce": "DESCUENTO: el futuro vale menos que el presente"}, {"paso": "Sumar todos los flujos descontados", "operacion": "¿Cuánto vale hoy la suma de todos los cobros y pagos futuros?", "produce": "ACUMULACIÓN: valor presente total"}, {"paso": "Si es positivo, la inversión crea valor. Si negativo, lo destruye.", "operacion": "Comparar con cero", "produce": "RESULTADO: ¿vale la pena invertir?"}]'::jsonb, 'La inversión genera más de lo que cuesta financiarla. Crea valor. Hazla.', 'La inversión cuesta más de lo que genera. Destruye valor. No la hagas.', '¿Cuánto valor crea o destruye esta inversión?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tir', 'TIR: Σ CFt/(1+TIR)^t = 0', 'finanzas', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','INVERTIR','TRANSFORMAR','ACUMULAR','COMPARAR','SELECCIONAR'], 'como VPN pero selecciona la tasa que hace VPN=0 → rentabilidad implícita de la inversión', 'adjetivo de rentabilidad implícita', 'bajo', 'alto', 'adjetivo de rentabilidad implícita', ARRAY['Asume que el óptimo existe y es alcanzable','Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Mercados suficientemente líquidos'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de rentabilidad implícita.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de rentabilidad implícita.', '¿rentabilidad implícita de la inversión?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('black_scholes', 'C = S·N(d1) - K·e^(-rT)·N(d2)', 'finanzas', ARRAY['VALORAR'], ARRAY['TRANSFORMAR','CONDICIONAR','COMPONER','ESCALAR','INVERTIR','TRANSFORMAR','CONDICIONAR','COMPONER','COMPARAR'], 'transforma a distribución normal, condiciona por probabilidad de ejercicio, compone precio×probabilidad para ambas partes, escala por descuento, compara → precio justo de la opción', 'sujeto (precio justo de un derecho futuro)', 'opción sin valor (muy out of the money)', 'opción valiosa (deep in the money)', 'precio justo de un derecho futuro', ARRAY['Volatilidad constante (no lo es)','Sin dividendos en versión básica','Mercados continuos y sin fricción'], '[{"paso": "Calcular probabilidad de ejercicio (N(d1), N(d2))", "operacion": "¿Cuán probable es que la opción acabe in the money?", "produce": "PROBABILIDAD"}, {"paso": "Ponderar: precio actual × probabilidad de subir - precio ejercicio × probabilidad de cobrar", "operacion": "Valor esperado descontado", "produce": "RESULTADO: precio justo de la opción"}]'::jsonb, 'La opción es valiosa: alta probabilidad de ejercerla con beneficio.', 'La opción apenas vale: improbable que se ejerza con beneficio.', '¿Cuál es el precio justo de este derecho a comprar/vender en el futuro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('var_parametrico', 'VaR = μ - z_α · σ', 'finanzas', ARRAY['MEDIR_RIESGO'], ARRAY['ESCALAR','COMPARAR'], 'escala desviación por z de confianza, compara con media → máxima pérdida probable', 'adjetivo de riesgo extremo', 'riesgo bajo', 'riesgo alto', 'pérdida máxima probable', ARRAY['Asume distribución normal (falla en colas pesadas)','No dice cuánto pierdes en el peor caso, solo el umbral'], '[{"paso": "Tomar media de retornos", "operacion": "Retorno esperado", "produce": "CENTRO"}, {"paso": "Restar z_α × desviación", "operacion": "Bajar z desviaciones estándar", "produce": "UMBRAL"}, {"paso": "RESULTADO: con X% de confianza, no perderás más que esto", "operacion": "Pérdida máxima probable", "produce": "RESULTADO"}]'::jsonb, 'Puedes perder mucho. Posición arriesgada.', 'Pérdida máxima contenida. Posición segura.', '¿Cuál es la máxima pérdida probable con X% de confianza?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ols', 'β = (X''X)⁻¹X''y', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','COMPONER'], 'compone X consigo misma (varianza de X), invierte, compone con X''y (covarianza) → efecto de X sobre Y', 'adjetivo de efecto causal (estimado)', 'sin efecto (β = 0)', 'efecto fuerte (β grande)', 'efecto estimado', ARRAY['Asume linealidad (Y = a + bX + error)','Asume que los errores son independientes de X (exogeneidad)','Asume que no hay variables omitidas correlacionadas con X','Isomorfo con IV/2SLS (COMPONER→INVERTIR→COMPONER) — misma gramática, diferente pureza'], '[{"paso": "Multiplicar X''X (varianza de X)", "operacion": "¿Cuánta variación hay en la variable explicativa?", "produce": "BASE: información disponible"}, {"paso": "Invertir X''X", "operacion": "Preparar para resolver el sistema", "produce": "INVERSIÓN: deshacer la varianza"}, {"paso": "Multiplicar por X''y (covarianza de X e Y)", "operacion": "¿Cuánto se mueven juntas X e Y?", "produce": "COMPOSICIÓN: relación cruda"}, {"paso": "Resultado: β = cuánto cambia Y por unidad de cambio en X", "operacion": "El efecto estimado", "produce": "RESULTADO: si X sube 1, Y sube β"}]'::jsonb, 'X tiene un efecto fuerte sobre Y. Un cambio pequeño en X produce un cambio grande en Y.', 'X tiene poco efecto sobre Y. Cambiar X apenas mueve Y.', '¿Cuánto cambia Y cuando X cambia en una unidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('r_cuadrado', 'R² = 1 - SSR/SST = 1 - Σei²/Σ(yi-ȳ)²', 'econometria', ARRAY['VERIFICAR','COMPARAR'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','COMPARAR'], 'acumula residuos al cuadrado, acumula variación total al cuadrado, normaliza, compara con 1 → cuánto explica el modelo', 'adjetivo de poder explicativo', 'no explica nada (R²=0)', 'explica todo (R²=1)', 'poder explicativo', ARRAY['No dice si el modelo es CORRECTO, solo si ajusta bien','R² alto con modelo incorrecto = sobreajuste','Nunca baja al añadir variables (por eso existe R² ajustado)'], '[{"paso": "Calcular variación total de Y (cuánto varía Y en total)", "operacion": "¿Cuánta variación hay que explicar?", "produce": "DENOMINADOR: variación total"}, {"paso": "Calcular variación residual (lo que el modelo NO explica)", "operacion": "¿Cuánto queda sin explicar?", "produce": "NUMERADOR: lo que falla"}, {"paso": "R² = 1 - (residual/total)", "operacion": "Proporción de variación explicada", "produce": "RESULTADO: fracción del mundo que entiendes"}]'::jsonb, 'El modelo explica la mayor parte de la variación. Entiendes bien qué mueve Y.', 'El modelo explica poco. Hay fuerzas que mueven Y que no estás capturando.', '¿Cuánta de la variación de Y captura mi modelo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('t_statistic', 't = β̂ / se(β̂)', 'econometria', ARRAY['VERIFICAR'], ARRAY['NORMALIZAR'], 'normaliza el coeficiente por su error estándar → cuántas veces más grande es el efecto que su incertidumbre', 'adjetivo de significancia (señal/ruido)', 'bajo', 'alto', 'adjetivo de significancia (señal/ruido)', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de significancia (señal/ruido).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de significancia.', '¿cuántas veces más grande es el efecto que su incertidumbre?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('did', 'τ = (Ȳ_T,post - Ȳ_T,pre) - (Ȳ_C,post - Ȳ_C,pre)', 'econometria', ARRAY['VERIFICAR'], ARRAY['COMPARAR','COMPARAR','COMPARAR'], 'compara antes/después en tratados, compara antes/después en control, compara ambos cambios → efecto neto del tratamiento', 'adjetivo de efecto causal (doble diferencia)', 'sin efecto del tratamiento', 'efecto causal fuerte', 'efecto causal', ARRAY['Asume TENDENCIAS PARALELAS: sin tratamiento, tratados y control habrían evolucionado igual','Este supuesto NO es testeable — es una apuesta de fe','Solo 3 operaciones COMPARAR — es la más limpia de las técnicas causales'], '[{"paso": "Medir cambio antes→después en el grupo tratado", "operacion": "¿Cuánto cambió el grupo que recibió el tratamiento?", "produce": "PRIMERA COMPARACIÓN: cambio bruto"}, {"paso": "Medir cambio antes→después en el grupo control", "operacion": "¿Cuánto cambió el grupo que NO recibió el tratamiento?", "produce": "SEGUNDA COMPARACIÓN: contrafactual"}, {"paso": "Restar: cambio_tratado - cambio_control", "operacion": "Eliminar lo que habría pasado de todos modos", "produce": "TERCERA COMPARACIÓN: efecto neto = efecto causal"}]'::jsonb, 'El tratamiento tuvo un efecto grande. La política/intervención funcionó.', 'El tratamiento no tuvo efecto o fue pequeño. La política no cambió nada.', '¿Cuál es el efecto CAUSAL del tratamiento, descontando lo que habría pasado sin él?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('mle', 'θ̂ = argmax Σ log f(xi|θ)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','TRANSFORMAR','ACUMULAR','SELECCIONAR'], 'condiciona probabilidad por parámetros, transforma a log, acumula (log-verosimilitud), selecciona máximo → parámetros más probables', 'sujeto (mejor estimación de los parámetros)', 'bajo valor', 'alto valor', 'sujeto (mejor estimación de los parámetros)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (mejor estimación de los parámetros).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿parámetros más probables?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gmm', 'θ̂ = argmin g(θ)''W g(θ)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','ESCALAR','SELECCIONAR'], 'condiciona momentos por parámetros, compone g×W×g (distancia ponderada), selecciona mínimo → parámetros que mejor cumplen las condiciones de momento', 'sujeto (estimación por momentos)', 'bajo valor', 'alto valor', 'sujeto (estimación por momentos)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (estimación por momentos).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿parámetros que mejor cumplen las condiciones de momento?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('iv_2sls', 'β̂_IV = (Z''X)⁻¹Z''y', 'econometria', ARRAY['VERIFICAR'], ARRAY['COMPONER','INVERTIR','COMPONER'], 'como OLS pero usando instrumento Z en lugar de X → efecto causal limpio de endogeneidad', 'adjetivo de efecto causal (instrumentado)', 'sin efecto causal', 'efecto causal fuerte', 'efecto causal limpio', ARRAY['Isomorfo con OLS (COMPONER→INVERTIR→COMPONER) — misma gramática, diferente pureza','Requiere instrumento válido (relevante + exógeno) — el talón de Aquiles'], '[{"paso": "Encontrar instrumento Z que afecta X pero no Y directamente", "operacion": "Variable que ''empuja'' X sin tocar Y", "produce": "INSTRUMENTO"}, {"paso": "Primera etapa: predecir X con Z", "operacion": "Purificar X de endogeneidad", "produce": "X limpia"}, {"paso": "Segunda etapa: regresar Y sobre X limpia", "operacion": "Efecto causal", "produce": "RESULTADO: cuánto cambia Y cuando X cambia por razones exógenas"}]'::jsonb, 'X tiene efecto causal fuerte sobre Y. Cambiar X cambiaría Y.', 'X no causa Y (o el efecto es pequeño). La correlación era espuria.', '¿Cuál es el efecto CAUSAL de X sobre Y, limpio de endogeneidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('prospect_value', 'v(x) = x^α si x≥0, -λ(-x)^β si x<0', 'conductual', ARRAY['MEDIR_RIESGO'], ARRAY['CONDICIONAR','TRANSFORMAR','ESCALAR'], 'condiciona por signo (ganancia/pérdida), transforma por potencia (concavidad/convexidad), escala pérdidas por λ≈2.5 → valor percibido asimétrico', 'adjetivo de valor percibido (pérdidas pesan 2.5× más)', 'pérdida percibida (dolor amplificado)', 'ganancia percibida (placer atenuado)', 'valor percibido asimétrico', ARRAY['Las pérdidas pesan ~2.5x más que las ganancias equivalentes','Sensibilidad decreciente: la diferencia entre 100→200 se siente más que 1000→1100','El punto de referencia (el ''cero'') no es objetivo — depende de expectativas'], '[{"paso": "¿Es ganancia o pérdida? (respecto al punto de referencia)", "operacion": "Clasificar por signo", "produce": "CONDICIÓN: ¿estás mejor o peor que tu referencia?"}, {"paso": "Si ganancia: aplicar x^0.88 (concavidad)", "operacion": "Sensibilidad decreciente: más no impresiona tanto", "produce": "TRANSFORMACIÓN: rendimientos decrecientes de alegría"}, {"paso": "Si pérdida: aplicar -2.25×|x|^0.88 (convexidad + amplificación)", "operacion": "El dolor es convexo Y amplificado", "produce": "TRANSFORMACIÓN: el dolor crece más que la alegría"}]'::jsonb, 'Ganancia: placer moderado. Cuanto más ganas, menos alegría marginal.', 'Pérdida: dolor intenso y desproporcionado. Perder 100€ duele 2.5x más que alegra ganar 100€.', '¿Cuánto vale esta situación PERCIBIDA, no objetivamente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('descuento_hiperbolico', 'D(t) = 1/(1+kt)', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ACUMULAR','INVERTIR'], 'escala tiempo por k, acumula con 1, invierte → descuento inconsistente (hoy pesa mucho, mañana casi igual que pasado mañana)', 'adjetivo de impaciencia inconsistente', 'paciente (descuenta poco)', 'impaciente (descuenta mucho)', 'impaciencia inconsistente', ARRAY['A diferencia del descuento exponencial, las preferencias CAMBIAN con el tiempo','Hoy prefiero €100 hoy a €110 mañana, pero prefiero €110 en 31 días a €100 en 30'], '[{"paso": "Multiplicar utilidad futura por 1/(1+kt)", "operacion": "Descontar el futuro", "produce": "DESCUENTO"}, {"paso": "A diferencia de δ^t (exponencial), 1/(1+kt) desciende rápido al principio y lento después", "operacion": "El presente es DESPROPORCIONADAMENTE más valioso", "produce": "INCONSISTENCIA"}, {"paso": "RESULTADO: explica procrastinación, adicción, falta de ahorro", "operacion": "Sesgo presente", "produce": "RESULTADO"}]'::jsonb, 'Muy impaciente: el presente domina cualquier decisión. Incapaz de comprometerse con el futuro.', 'Relativamente paciente: capaz de sacrificar hoy por mañana.', '¿Cuánto devalúa el futuro de forma inconsistente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('probabilidad_ponderada', 'w(p) = p^γ / (p^γ + (1-p)^γ)^(1/γ)', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','TRANSFORMAR','ACUMULAR','TRANSFORMAR','NORMALIZAR'], 'transforma probabilidades (sobrepondera raros, infrapondera frecuentes) → percepción distorsionada del riesgo', 'adjetivo de distorsión probabilística', 'bajo', 'alto', 'adjetivo de distorsión probabilística', ARRAY['La normalización asume que el denominador es significativo','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de distorsión probabilística.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de distorsión probabilística.', '¿percepción distorsionada del riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('exceso_demanda', 'z(p) = Σ x_i(p) - Σ ω_i', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','ACUMULAR','COMPARAR'], 'acumula todas las demandas, acumula todas las dotaciones, compara → cuánto sobra o falta en el mercado', 'adjetivo de desequilibrio de mercado', 'bajo', 'alto', 'adjetivo de desequilibrio de mercado', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de desequilibrio de mercado.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de desequilibrio de mercado.', '¿cuánto sobra o falta en el mercado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ley_walras', 'p·z(p) = 0', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR'], 'compone precio×exceso por cada bien, acumula → el valor total del exceso siempre es cero', 'identidad (restricción del sistema)', 'siempre se cumple', 'siempre se cumple', 'identidad (restricción del sistema)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad (restricción del sistema).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad.', '¿el valor total del exceso siempre es cero?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bienestar_utilitarista', 'W = Σ u_i(x_i)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR'], 'acumula las utilidades de todos los individuos → bienestar total', 'sujeto (bienestar social agregado)', 'bajo valor', 'alto valor', 'sujeto (bienestar social agregado)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (bienestar social agregado).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿bienestar total?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bienestar_rawls', 'W = min_i {u_i(x_i)}', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['SELECCIONAR'], 'selecciona la utilidad mínima → bienestar del peor individuo', 'sujeto (bienestar del más desfavorecido)', 'bajo valor', 'alto valor', 'sujeto (bienestar del más desfavorecido)', ARRAY['Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (bienestar del más desfavorecido).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿bienestar del peor individuo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('indice_atkinson', 'A = 1 - [Σ(y_i/ȳ)^(1-ε)/n]^(1/(1-ε))', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','TRANSFORMAR','COMPARAR'], 'normaliza rentas por media, transforma por aversión ε, acumula, normaliza, transforma de vuelta, compara con 1 → desigualdad con preferencia ética explícita', 'adjetivo de desigualdad (con juicio de valor)', 'bajo', 'alto', 'adjetivo de desigualdad (con juicio de valor)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de desigualdad (con juicio de valor).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de desigualdad.', '¿desigualdad con preferencia ética explícita?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('indice_theil', 'T = (1/n)Σ (y_i/ȳ)·ln(y_i/ȳ)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','COMPONER','ACUMULAR','NORMALIZAR'], 'normaliza rentas por media, transforma a log, compone ratio×log, acumula, normaliza → desigualdad descomponible por grupos', 'adjetivo de desigualdad descomponible', 'bajo', 'alto', 'adjetivo de desigualdad descomponible', ARRAY['La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de desigualdad descomponible.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de desigualdad descomponible.', '¿desigualdad descomponible por grupos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bellman', 'V(x) = max_a {r(x,a) + β·V(f(x,a))}', 'optimizacion', ARRAY['PRESCRIBIR','OPTIMIZAR'], ARRAY['COMPONER','ESCALAR','ACUMULAR','SELECCIONAR'], 'compone acción×estado, escala futuro por descuento, acumula presente+futuro, selecciona máximo → valor óptimo del estado', 'sujeto (valor fundamental de una situación)', 'estado sin valor (callejón sin salida)', 'estado muy valioso (posición privilegiada)', 'valor de una situación', ARRAY['Asume que puedes evaluar el futuro (conoces la función de transición)','Descuenta el futuro por β — el presente vale más','Principio de optimalidad: si la decisión global es óptima, cada subdecisión también lo es'], '[{"paso": "Para cada acción posible, calcular recompensa inmediata", "operacion": "¿Cuánto gano AHORA?", "produce": "VALOR PRESENTE"}, {"paso": "Para cada acción, calcular el valor del estado al que llego × descuento", "operacion": "¿Cuánto vale el FUTURO al que me lleva esta acción?", "produce": "VALOR FUTURO descontado"}, {"paso": "Sumar presente + futuro", "operacion": "¿Cuánto vale cada acción en total?", "produce": "VALOR TOTAL de cada opción"}, {"paso": "Elegir la acción con mayor valor total", "operacion": "¿Cuál es la mejor opción?", "produce": "RESULTADO: decisión óptima + valor del estado"}]'::jsonb, 'Estás en una buena posición. Tienes opciones valiosas. El futuro desde aquí es prometedor.', 'Estás en una mala posición. Tus opciones son pobres. Difícil mejorar desde aquí.', '¿Cuánto vale estar en esta situación, considerando todas las decisiones futuras óptimas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bellman_estocastica', 'V(x) = max_a {r(x,a) + β·E[V(x'')|x,a]}', 'optimizacion', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ESCALAR','CONDICIONAR','ACUMULAR','SELECCIONAR'], 'como Bellman pero condiciona el futuro a la incertidumbre → decisión óptima bajo riesgo', 'sujeto (valor fundamental bajo incertidumbre)', 'bajo valor', 'alto valor', 'sujeto (valor fundamental bajo incertidumbre)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','El problema tiene solución factible'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (valor fundamental bajo incertidumbre).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿decisión óptima bajo riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lagrangiano', 'L = f(x) - Σ λ_j·g_j(x)', 'optimizacion', ARRAY['PRESCRIBIR','OPTIMIZAR'], ARRAY['ESCALAR','COMPARAR'], 'escala restricciones por precios sombra, compara con objetivo → función auxiliar para optimizar con restricciones', 'herramienta (transforma problema restringido en libre)', 'restricción inactiva (no muerde)', 'restricción activa (limita el óptimo)', 'coste de la restricción', ARRAY['λ (multiplicador) = precio sombra: cuánto mejoraría el óptimo si relajaras la restricción 1 unidad'], '[{"paso": "Construir L = f(x) - λ·g(x)", "operacion": "Objetivo - penalización por violar restricción", "produce": "FUNCIÓN AUXILIAR"}, {"paso": "Derivar respecto a x: ∂f/∂x = λ·∂g/∂x", "operacion": "En el óptimo, el gradiente del objetivo es proporcional al de la restricción", "produce": "CONDICIÓN"}, {"paso": "λ = cuánto vale relajar la restricción", "operacion": "Precio sombra", "produce": "RESULTADO: cuánto pagarías por una unidad más de recurso"}]'::jsonb, 'La restricción muerde fuerte. Relajarla mejoraría mucho el resultado. Recurso escaso y valioso.', 'La restricción no muerde. Hay holgura. El recurso no es limitante.', '¿Cuánto mejoraría el resultado si tuviera una unidad más de recurso?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kkt', '∇f = Σλ∇g + Σμ∇h; μ≥0; μ·h(x)=0', 'optimizacion', ARRAY['PRESCRIBIR','OPTIMIZAR'], ARRAY['DERIVAR','ESCALAR','COMPARAR','CONDICIONAR'], 'deriva objetivo, escala restricciones por multiplicadores, compara gradientes, condiciona por complementariedad → óptimo con desigualdades', 'condición de óptimo (cuándo parar)', 'interior (lejos de límites)', 'frontera (en el límite)', 'naturaleza del óptimo', ARRAY['Generalizan Lagrange a desigualdades','Complementariedad: o la restricción muerde o su multiplicador es cero'], '[{"paso": "Verificar condiciones de primer orden", "operacion": "Gradiente = combinación de gradientes de restricciones", "produce": "NECESIDAD"}, {"paso": "Verificar complementariedad", "operacion": "Restricción activa ↔ multiplicador > 0", "produce": "SELECCIÓN de restricciones activas"}, {"paso": "RESULTADO: qué restricciones limitan y cuáles son irrelevantes", "operacion": "Mapa de cuellos de botella", "produce": "RESULTADO"}]'::jsonb, 'El óptimo está en el borde. Las restricciones importan.', 'El óptimo está en el interior. Las restricciones no limitan.', '¿Qué restricciones limitan el óptimo y cuáles son irrelevantes?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hjb', 'ρV(x) = max_a {r(x,a) + V''(x)·f(x,a)}', 'optimizacion', ARRAY['OPTIMIZAR'], ARRAY['DERIVAR','COMPONER','ACUMULAR','SELECCIONAR','ESCALAR'], 'Bellman en tiempo continuo: deriva valor, compone con dinámica, acumula flujo+cambio, selecciona óptimo, escala por impaciencia', 'sujeto (valor en tiempo continuo)', 'bajo valor', 'alto valor', 'sujeto (valor en tiempo continuo)', ARRAY['Asume que el óptimo existe y es alcanzable','Asume diferenciabilidad — la función es suave','El problema tiene solución factible'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "PUNTO ÓPTIMO"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (valor en tiempo continuo).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿sujeto (valor en tiempo continuo)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('punto_fijo_brouwer', 'f:K→K continua, K compacto convexo → ∃x*: f(x*)=x*', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','SELECCIONAR'], 'condiciona por propiedades del espacio, selecciona punto donde la función se reproduce a sí misma → existencia de equilibrio', 'existencia (garantía de que el equilibrio existe)', 'sin equilibrio (no hay punto fijo)', 'equilibrio existe (hay punto fijo)', 'existencia de solución', ARRAY['Solo garantiza EXISTENCIA, no unicidad ni estabilidad','Requiere compacidad + convexidad + continuidad'], '[{"paso": "Verificar que el espacio es compacto y convexo", "operacion": "¿El problema está bien definido?", "produce": "CONDICIÓN"}, {"paso": "Verificar que la función es continua", "operacion": "¿Las respuestas cambian suavemente?", "produce": "CONDICIÓN"}, {"paso": "EXISTE punto donde f(x*)=x*", "operacion": "La función se reproduce a sí misma", "produce": "RESULTADO: el equilibrio existe (aunque no sepamos dónde)"}]'::jsonb, 'Condiciones cumplidas: equilibrio existe. Buscar es fructífero.', 'Condiciones no cumplidas: el equilibrio puede no existir. No buscar a ciegas.', '¿Existe un equilibrio en este sistema?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('contraccion_banach', 'T contracción → ∃! x*=T(x*), T^n(x_0)→x*', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','SELECCIONAR'], 'compara iteraciones sucesivas (se acercan), transforma por contracción, selecciona punto fijo → existencia + unicidad + convergencia', 'existencia + unicidad + algoritmo', 'no converge (diverge)', 'converge (al punto fijo)', 'convergencia algorítmica', ARRAY['Más fuerte que Brouwer: existencia + unicidad + convergencia + algoritmo','Requiere contracción: cada iteración acerca al punto fijo'], '[{"paso": "Verificar que cada iteración reduce la distancia en factor β<1", "operacion": "¿Se acerca?", "produce": "CONTRACCIÓN"}, {"paso": "Iterar: T(T(T(...x₀)))", "operacion": "Repetir", "produce": "ALGORITMO"}, {"paso": "RESULTADO: converge al ÚNICO punto fijo", "operacion": "Garantía triple", "produce": "RESULTADO"}]'::jsonb, 'Converge rápido (β pequeño). Pocas iteraciones necesarias.', 'Converge lento (β cercano a 1). Muchas iteraciones.', '¿Este proceso iterativo converge y a qué velocidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('control_sintetico', 'Ŷ₁ = Σ w_j·Y_j, w* = argmin ||X₁-X₀w||', 'econometria', ARRAY['VERIFICAR'], ARRAY['ESCALAR','ACUMULAR','COMPARAR','SELECCIONAR'], 'escala controles por pesos óptimos, acumula → contrafactual sintético, compara con tratado → efecto causal', 'adjetivo de efecto causal (contrafactual construido)', 'sin efecto', 'efecto grande', 'efecto causal por contrafactual construido', ARRAY['Construye un ''clon'' del tratado con combinación de controles','No funciona si no hay buenos controles'], '[{"paso": "Encontrar pesos óptimos para controles que repliquen al tratado pre-tratamiento", "operacion": "Construir gemelo sintético", "produce": "CONTRAFACTUAL"}, {"paso": "Comparar tratado con su gemelo post-tratamiento", "operacion": "¿Qué habría pasado sin tratamiento?", "produce": "RESULTADO: efecto = diferencia entre real y sintético"}]'::jsonb, 'El tratamiento tuvo efecto grande. El real diverge mucho de su gemelo.', 'El tratamiento no tuvo efecto. El real y su gemelo evolucionan igual.', '¿Qué habría pasado sin la intervención?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('doubly_robust', 'τ̂ = (1/n)Σ[m̂₁(x)-m̂₀(x) + D(Y-m̂₁)/ê - (1-D)(Y-m̂₀)/(1-ê)]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR','COMPARAR','NORMALIZAR','ACUMULAR','NORMALIZAR'], 'compara outcomes estimados, normaliza por propensity score, acumula correcciones → efecto causal robusto a errores en un modelo', 'adjetivo de efecto causal (doblemente robusto)', 'bajo', 'alto', 'adjetivo de efecto causal (doblemente robusto)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de efecto causal (doblemente robusto).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de efecto causal.', '¿efecto causal robusto a errores en un modelo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kalman', 'x̂ = x̂_pred + K·(y - H·x̂_pred); K = PH''(HPH''+R)⁻¹', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR','COMPONER','INVERTIR','ESCALAR','ACUMULAR'], 'compone predicción×modelo, compara con observación (innovación), compone incertidumbres, invierte para ponderar, escala corrección → estimación óptima de estado oculto', 'sujeto (mejor estimación del estado real)', 'bajo valor', 'alto valor', 'sujeto (mejor estimación del estado real)', ARRAY['Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (mejor estimación del estado real).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿estimación óptima de estado oculto?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('garch', 'σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}', 'econometria', ARRAY['PREDECIR','MEDIR_RIESGO'], ARRAY['TRANSFORMAR','ESCALAR','ESCALAR','ACUMULAR'], 'transforma error al cuadrado, escala por reacción α, escala persistencia por β, acumula con base ω → volatilidad que se alimenta de sí misma', 'adjetivo de volatilidad auto-alimentada', 'volatilidad baja y estable', 'volatilidad alta y autoalimentada', 'volatilidad condicional', ARRAY['La volatilidad de hoy depende de la volatilidad y shocks de ayer','Captura clusters de volatilidad (periodos tranquilos y periodos turbulentos)'], '[{"paso": "Tomar shock cuadrado del período anterior (ε²)", "operacion": "¿Hubo sorpresa ayer?", "produce": "REACCIÓN a noticias"}, {"paso": "Tomar volatilidad del período anterior (σ²)", "operacion": "¿Era volátil ayer?", "produce": "PERSISTENCIA"}, {"paso": "Ponderar y sumar", "operacion": "Volatilidad de hoy = reacción + inercia + base", "produce": "RESULTADO: cuánto fluctuará hoy dado lo que pasó ayer"}]'::jsonb, 'Período turbulento: la volatilidad se autoalimenta. Shocks grandes generan más volatilidad.', 'Período tranquilo: poca reacción a noticias, baja inercia.', '¿Cuánto fluctuará hoy dado lo que pasó ayer?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('sdf', 'p = E[m·x], m = β·u''(c₁)/u''(c₀)', 'finanzas', ARRAY['VALORAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','ESCALAR','COMPONER','CONDICIONAR','ACUMULAR'], 'deriva utilidad hoy y mañana, normaliza (ratio), escala por descuento, compone con pago, condiciona por información, acumula → precio de cualquier activo', 'sujeto universal (precio de TODO activo financiero)', 'bajo valor', 'alto valor', 'sujeto universal (precio de TODO activo financiero', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Mercados suficientemente líquidos'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto universal (precio de TODO activo financiero).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto universal.', '¿precio de cualquier activo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('modigliani_miller', 'V_L = V_U (sin fricciones)', 'finanzas', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR'], 'compara valor apalancado con no apalancado → la estructura de capital no importa', 'identidad (irrelevancia)', 'siempre se cumple', 'siempre se cumple', 'identidad (irrelevancia)', ARRAY['La comparación asume que las escalas son compatibles','Mercados suficientemente líquidos'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad (irrelevancia).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad.', '¿la estructura de capital no importa?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ito_lemma', 'df = (∂f/∂t + μS·∂f/∂S + ½σ²S²·∂²f/∂S²)dt + σS·∂f/∂S·dW', 'finanzas', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','DERIVAR','COMPONER','TRANSFORMAR','COMPONER','ACUMULAR'], 'deriva por tiempo, deriva por precio (1ª y 2ª orden), compone con drift y difusión, transforma cuadrático, acumula → cómo cambia cualquier función de un activo aleatorio', 'herramienta universal (cadena de regla estocástica)', 'no aplica', 'muy útil', 'herramienta universal (cadena de regla estocástica', ARRAY['Asume diferenciabilidad — la función es suave','Mercados suficientemente líquidos'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta universal (cadena de regla estocástica).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta universal.', '¿cómo cambia cualquier función de un activo aleatorio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('frontera_eficiente', 'min w''Σw s.a. w''μ=μ̄, w''1=1', 'finanzas', ARRAY['OPTIMIZAR'], ARRAY['COMPONER','CONDICIONAR','SELECCIONAR'], 'compone pesos×varianzas, condiciona por retorno objetivo, selecciona mínimo riesgo → portfolio óptimo', 'prescripción (cómo invertir dado un objetivo)', 'no intervenir', 'intervenir fuerte', 'prescripción (cómo invertir dado un objetivo)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Mercados suficientemente líquidos'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (cómo invertir dado un objetivo).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿portfolio óptimo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('fehr_schmidt', 'U_i = x_i - α·Σmax(x_j-x_i,0)/(n-1) - β·Σmax(x_i-x_j,0)/(n-1)', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','ACOTAR','ACUMULAR','NORMALIZAR','ESCALAR','COMPARAR','ACOTAR','ACUMULAR','NORMALIZAR','ESCALAR','COMPARAR'], 'compara con cada otro, acota a positivos (envidia), acumula, normaliza, escala por aversión; repite para culpa; compara con pago propio → utilidad que sufre por desigualdad', 'adjetivo de preferencia social (envidia + culpa)', 'bajo', 'alto', 'adjetivo de preferencia social (envidia + culpa)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Poner límites", "operacion": "max(0,x) o clamp", "produce": "ACOTADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Poner límites", "operacion": "max(0,x) o clamp", "produce": "ACOTADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de preferencia social (envidia + culpa).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de preferencia social.', '¿utilidad que sufre por desigualdad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('quantal_response', 'σ_i(s) = exp(λ·Eπ_i(s)) / Σ exp(λ·Eπ_i(s''))', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','TRANSFORMAR','NORMALIZAR'], 'escala payoff por racionalidad λ, transforma a exponencial, normaliza (softmax) → equilibrio con errores', 'adjetivo de racionalidad limitada (λ→∞ = Nash, λ→0 = aleatorio)', 'bajo', 'alto', 'adjetivo de racionalidad limitada (λ→∞ = Nash, λ→0', ARRAY['La normalización asume que el denominador es significativo','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de racionalidad limitada (λ→∞ = Nash, λ→0 = aleatorio).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de racionalidad limitada.', '¿equilibrio con errores?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ar1', 'y_t = c + φ·y_{t-1} + ε_t', 'econometria', ARRAY['PREDECIR'], ARRAY['ESCALAR','ACUMULAR'], 'escala valor anterior por persistencia φ, acumula con constante + shock → cuánto del pasado permanece en el presente', 'adjetivo de persistencia (φ→1 = permanente, φ→0 = transitorio)', 'bajo', 'alto', 'adjetivo de persistencia (φ→1 = permanente, φ→0 = ', ARRAY['Los datos son representativos de la población'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de persistencia (φ→1 = permanente, φ→0 = transitorio).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de persistencia.', '¿cuánto del pasado permanece en el presente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('var', 'Y_t = c + A₁Y_{t-1} + ... + A_pY_{t-p} + ε_t', 'econometria', ARRAY['PREDECIR'], ARRAY['COMPONER','ACUMULAR'], 'compone vectores pasados por matrices de impacto, acumula → sistema completo de interdependencias temporales', 'sistema (cómo todo afecta a todo en el tiempo)', 'simple', 'complejo', 'sistema (cómo todo afecta a todo en el tiempo)', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema (cómo todo afecta a todo en el tiempo).', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema.', '¿sistema completo de interdependencias temporales?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cointegracion', 'β''Y_t ~ I(0) aunque Y_t ~ I(1)', 'econometria', ARRAY['PREDECIR'], ARRAY['COMPONER','TRANSFORMAR','COMPARAR'], 'compone variables no estacionarias por vector β, transforma → resultado estacionario, compara con I(0) → relación de largo plazo entre variables que deambulan', 'adjetivo de relación estable de largo plazo', 'bajo', 'alto', 'adjetivo de relación estable de largo plazo', ARRAY['La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de relación estable de largo plazo.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de relación estable de largo plazo.', '¿relación de largo plazo entre variables que deambulan?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('impulso_respuesta', 'IRF: Y_{t+h} = Σ Ψ_s·ε_{t+h-s}', 'econometria', ARRAY['PREDECIR'], ARRAY['COMPONER','ACUMULAR'], 'compone shocks pasados por matrices de respuesta, acumula → efecto dinámico completo de un shock', 'narrativa (cómo se propaga un shock en el tiempo)', 'sin efecto', 'efecto grande y dinámico', 'narrativa (cómo se propaga un shock en el tiempo)', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto grande y dinámico''. narrativa (cómo se propaga un shock en el tiempo).', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a narrativa.', '¿efecto dinámico completo de un shock?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('nkpc', 'π_t = β·E_t[π_{t+1}] + κ·x_t', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','ESCALAR','ESCALAR','ACUMULAR'], 'condiciona inflación futura por información actual, escala por descuento, escala output gap por pendiente, acumula → inflación como expectativas + presión real', 'adjetivo de presión inflacionaria (expectativas + gap)', 'bajo', 'alto', 'adjetivo de presión inflacionaria (expectativas + ', ARRAY['Asume que las condiciones son observables y verificables','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de presión inflacionaria (expectativas + gap).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de presión inflacionaria.', '¿inflación como expectativas + presión real?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('is_nk', 'x_t = E_t[x_{t+1}] - (1/σ)(i_t - E_t[π_{t+1}] - r^n)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR','INVERTIR','ESCALAR','COMPARAR'], 'condiciona futuro, compara tipo de interés con natural, invierte elasticidad, escala → output gap como función del tipo real vs natural', 'adjetivo de posición cíclica', 'bajo', 'alto', 'adjetivo de posición cíclica', ARRAY['Asume que las condiciones son observables y verificables','Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de posición cíclica.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de posición cíclica.', '¿output gap como función del tipo real vs natural?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('calvo_pricing', 'p* = (1-βθ)Σ(βθ)^k E_t[mc_{t+k}]', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','ESCALAR','TRANSFORMAR','ACUMULAR'], 'condiciona costes futuros, escala por descuento×rigidez, transforma a serie geométrica, acumula → precio óptimo mirando al futuro', 'sujeto (precio que fijaría si pudiera cambiar)', 'bajo valor', 'alto valor', 'sujeto (precio que fijaría si pudiera cambiar)', ARRAY['Asume que las condiciones son observables y verificables','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio que fijaría si pudiera cambiar).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿precio óptimo mirando al futuro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('dyn_deuda', 'ΔB/Y = (r-g)·B/Y - pb', 'macro', ARRAY['PREDECIR','MEDIR_RIESGO'], ARRAY['COMPARAR','COMPONER','COMPARAR'], 'compara tipo de interés con crecimiento, compone con ratio deuda, compara con superávit primario → si la deuda crece o se reduce', 'adjetivo de sostenibilidad fiscal (r>g = diverge, r<g = converge)', 'deuda converge (sostenible)', 'deuda diverge (insostenible)', 'dinámica fiscal', ARRAY['r-g es el factor clave: si tipo de interés > crecimiento, la deuda crece sola','El superávit primario es lo que el gobierno controla'], '[{"paso": "Comparar tipo de interés (r) con crecimiento (g)", "operacion": "¿La deuda crece más rápido que la economía?", "produce": "DINÁMICA automática"}, {"paso": "Multiplicar (r-g) por ratio deuda actual", "operacion": "¿Cuánto sube la deuda por inercia?", "produce": "EFECTO bola de nieve"}, {"paso": "Restar superávit primario", "operacion": "¿Cuánto compensa el gobierno con impuestos-gasto?", "produce": "RESULTADO: si la deuda sube o baja"}]'::jsonb, 'r>g y déficit: la deuda explota. Espiral fiscal. Crisis inminente sin ajuste.', 'g>r o superávit: la deuda se reduce sola. Sostenible.', '¿La deuda está en trayectoria sostenible o explosiva?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ramsey_euler', 'ċ/c = (1/σ)[f''(k) - δ - ρ]', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPARAR','COMPARAR','INVERTIR','COMPONER'], 'deriva utilidad, compara productividad marginal con depreciación+impaciencia, invierte aversión al riesgo, compone → velocidad óptima de cambio del consumo', 'prescripción (cuánto debe crecer el consumo)', 'no intervenir', 'intervenir fuerte', 'prescripción (cuánto debe crecer el consumo)', ARRAY['Asume diferenciabilidad — la función es suave','Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (cuánto debe crecer el consumo).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿velocidad óptima de cambio del consumo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hodrick_prescott', 'min Σ(y_t-τ_t)² + λΣ[(τ_{t+1}-τ_t)-(τ_t-τ_{t-1})]²', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','COMPARAR','COMPARAR','TRANSFORMAR','ACUMULAR','ESCALAR','ACUMULAR','SELECCIONAR'], 'compara dato con tendencia (ajuste), transforma al cuadrado, acumula; compara cambios de tendencia (suavidad), transforma, acumula, escala por λ; suma ambos, selecciona mínimo → separa tendencia de ciclo', 'descomposición (trend + cycle)', 'un solo factor', 'múltiples factores', 'descomposición (trend + cycle)', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición (trend + cycle).', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición.', '¿separa tendencia de ciclo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lln', 'X̄_n → E[X] (p o a.s.)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','NORMALIZAR','COMPARAR'], 'acumula observaciones, normaliza por n, compara con esperanza → la media muestral converge a la real', 'garantía (los datos eventualmente revelan la verdad)', 'datos insuficientes (muestra pequeña)', 'datos revelan la verdad (muestra grande)', 'convergencia a la realidad', ARRAY['Requiere independencia','No dice cuán rápido converge (eso es el TCL)'], '[{"paso": "Acumular observaciones", "operacion": "Más datos", "produce": "ACUMULACIÓN"}, {"paso": "La media muestral converge a la esperanza", "operacion": "Los datos revelan la verdad", "produce": "RESULTADO: con suficientes datos, sabrás la respuesta correcta"}]'::jsonb, 'Muestra grande: la media muestral ES (casi) la real. Confía en los datos.', 'Muestra pequeña: la media muestral puede estar lejos de la real. No confíes aún.', '¿Tengo suficientes datos para que la media muestral sea fiable?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tcl', '√n(X̄-μ)/σ →d N(0,1)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','NORMALIZAR','COMPARAR','NORMALIZAR','TRANSFORMAR'], 'acumula, normaliza (media), compara con esperanza, normaliza por desviación, transforma por √n → la distribución de la media es normal', 'garantía (la incertidumbre se puede cuantificar)', 'distribución desconocida', 'distribución normal', 'normalidad asintótica', ARRAY['Funciona con CUALQUIER distribución original (si tiene varianza finita)','La velocidad de convergencia depende de la distribución original'], '[{"paso": "Tomar medias de muestras repetidas", "operacion": "Distribución de medias muestrales", "produce": "DISTRIBUCIÓN del estimador"}, {"paso": "Con n grande, esta distribución se parece a una normal", "operacion": "Campana de Gauss", "produce": "FORMA"}, {"paso": "RESULTADO: puedes usar intervalos de confianza y tests normales", "operacion": "Inferencia estadística", "produce": "RESULTADO"}]'::jsonb, 'n grande: la distribución es normal. Tests estándar son válidos.', 'n pequeño: la distribución puede no ser normal. Tests pueden ser incorrectos.', '¿Puedo usar estadística normal para hacer inferencia?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('jensen', 'E[g(X)] ≥ g(E[X]) si g convexa', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','CONDICIONAR','COMPARAR'], 'transforma por función convexa, condiciona por convexidad, compara esperanza de transformada con transformada de esperanza → la desigualdad fundamental de la aversión al riesgo', 'restricción (por qué los aversos al riesgo pagan prima)', 'función lineal (igualdad)', 'función convexa/cóncava (desigualdad estricta)', 'efecto de la curvatura', ARRAY['Fundamental para entender aversión al riesgo','Si u es cóncava: E[u(X)] < u(E[X]) → la gente prefiere la certeza'], '[{"paso": "Aplicar función convexa/cóncava a variable aleatoria", "operacion": "Transformar", "produce": "TRANSFORMACIÓN"}, {"paso": "Comparar E[f(X)] con f(E[X])", "operacion": "¿La esperanza de la transformación = transformación de la esperanza?", "produce": "COMPARACIÓN"}, {"paso": "NO: la curvatura crea gap", "operacion": "El gap ES la prima de riesgo", "produce": "RESULTADO: por qué los aversos al riesgo pagan seguro"}]'::jsonb, 'Gran curvatura: gran desigualdad. Las personas pagan mucho por certeza.', 'Poca curvatura (casi lineal): poca diferencia entre riesgo y certeza.', '¿Cuánto afecta la curvatura de las preferencias a las decisiones bajo riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('vickrey', 'b(v) = v (estrategia dominante)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'pujas tu valor real — ninguna operación, la verdad es óptima', 'identidad (la verdad es la estrategia óptima)', 'siempre se cumple', 'siempre se cumple', 'identidad (la verdad es la estrategia óptima)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Esta fórmula es un resultado teórico/imposibilidad", "operacion": "No requiere cálculo", "produce": "PROPIEDAD del sistema"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad (la verdad es la estrategia óptima).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad.', '¿identidad (la verdad es la estrategia óptima)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('myerson_subasta', 'ψ(v) = v - (1-F(v))/f(v)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','INVERTIR','COMPARAR'], 'normaliza la distribución (hazard rate), invierte, compara con valor real → valor virtual (lo que realmente vale extraer del comprador)', 'sujeto (valor virtual — la verdad económica detrás del valor reportado)', 'bajo valor', 'alto valor', 'sujeto (valor virtual — la verdad económica detrás', ARRAY['Asume invertibilidad — la función tiene inversa','La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (valor virtual — la verdad económica detrás del valor reportado).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿valor virtual (lo que realmente vale extraer del comprador)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('vcg', 't_i = Σ_{j≠i} v_j(q*) - Σ_{j≠i} v_j(q*_{-i})', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','ACUMULAR','COMPARAR'], 'acumula valor de los demás con i, acumula sin i, compara → cuánto cambia el bienestar de otros por la presencia de i', 'adjetivo de externalidad (cuánto afectas a los demás)', 'bajo', 'alto', 'adjetivo de externalidad (cuánto afectas a los dem', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de externalidad (cuánto afectas a los demás).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de externalidad.', '¿cuánto cambia el bienestar de otros por la presencia de i?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('utilidad_indirecta', 'v(p,w) = max_{p·x≤w} u(x)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','SELECCIONAR'], 'condiciona por presupuesto, selecciona máximo → máxima satisfacción posible', 'sujeto (techo de bienestar dada la restricción)', 'bajo valor', 'alto valor', 'sujeto (techo de bienestar dada la restricción)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (techo de bienestar dada la restricción).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿máxima satisfacción posible?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('identidad_roy', 'x_i = -(∂v/∂p_i)/(∂v/∂w)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','TRANSFORMAR'], 'deriva utilidad indirecta por precio y por renta, divide, invierte signo → demanda desde arriba', 'herramienta (demanda sin resolver el problema del consumidor)', 'no aplica', 'muy útil', 'herramienta (demanda sin resolver el problema del ', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (demanda sin resolver el problema del consumidor).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿demanda desde arriba?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('funcion_gasto', 'e(p,ū) = min_{u(x)≥ū} p·x', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','SELECCIONAR'], 'condiciona por utilidad mínima, compone precio×cantidad, selecciona mínimo → cuánto cuesta ser feliz', 'sujeto (coste de la felicidad)', 'bajo valor', 'alto valor', 'sujeto (coste de la felicidad)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (coste de la felicidad).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿cuánto cuesta ser feliz?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('slutsky', '∂x/∂p = ∂h/∂p - x·∂x/∂w', 'micro', ARRAY['DESCOMPONER'], ARRAY['DERIVAR','DERIVAR','COMPONER','COMPARAR'], 'deriva efecto sustitución, deriva efecto renta, compone cantidad×renta, compara → descompone por qué cambias lo que compras', 'descomposición (sustitución + renta)', 'un solo factor', 'múltiples factores', 'descomposición (sustitución + renta)', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición (sustitución + renta).', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición.', '¿descompone por qué cambias lo que compras?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('aversion_riesgo_arrow_pratt', 'r_A(x) = -u''''(x)/u''(x)', 'micro', ARRAY['MEDIR_RIESGO'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','TRANSFORMAR'], 'deriva 2x la utilidad, normaliza por la primera derivada, invierte signo → cuánto te disgusta el riesgo', 'adjetivo de personalidad frente al riesgo', 'bajo', 'alto', 'adjetivo de personalidad frente al riesgo', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de personalidad frente al riesgo.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de personalidad frente al riesgo.', '¿cuánto te disgusta el riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('prima_riesgo_arrowpratt', 'π ≈ ½·r_A·Var(x)', 'micro', ARRAY['MEDIR_RIESGO'], ARRAY['COMPONER','ESCALAR'], 'compone aversión×varianza, escala por ½ → cuánto pagas para NO tener incertidumbre', 'adjetivo de coste del miedo', 'bajo', 'alto', 'adjetivo de coste del miedo', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de coste del miedo.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de coste del miedo.', '¿cuánto pagas para NO tener incertidumbre?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equivalente_cierto', 'CE: u(CE) = E[u(x)]', 'micro', ARRAY['VALORAR'], ARRAY['CONDICIONAR','ACUMULAR','INVERTIR'], 'condiciona por incertidumbre, acumula utilidades esperadas, invierte la función → riqueza segura equivalente a la lotería', 'sujeto (cuánto vale la certeza)', 'bajo valor', 'alto valor', 'sujeto (cuánto vale la certeza)', ARRAY['Asume que las condiciones son observables y verificables','Asume invertibilidad — la función tiene inversa','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (cuánto vale la certeza).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿riqueza segura equivalente a la lotería?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('dominancia_estocastica_1', 'F ≥_FSD G ⟺ F(x) ≤ G(x) ∀x', 'micro', ARRAY['COMPARAR'], ARRAY['COMPARAR'], 'compara distribuciones punto a punto → F da más probabilidad a resultados buenos', 'ordenamiento (esta opción domina a la otra para todos)', 'inferior', 'superior', 'ordenamiento (esta opción domina a la otra para to', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''superior''. ordenamiento (esta opción domina a la otra para todos).', 'Valor bajo → cerca del polo ''inferior''. Opuesto a ordenamiento.', '¿F da más probabilidad a resultados buenos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('agregacion_engel', 'Σ s_i·ε_wi = 1', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR'], 'compone participación×elasticidad-renta por bien, acumula → la suma ponderada siempre es 1', 'identidad (restricción contable del consumidor)', 'siempre se cumple', 'siempre se cumple', 'identidad (restricción contable del consumidor)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad (restricción contable del consumidor).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad.', '¿la suma ponderada siempre es 1?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('funcion_coste', 'C(w,y) = min_{f(x)≥y} w·x', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','SELECCIONAR'], 'condiciona por output mínimo, compone precio×input, selecciona mínimo → coste de producir', 'sujeto (precio de crear)', 'bajo valor', 'alto valor', 'sujeto (precio de crear)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio de crear).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿coste de producir?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lema_shephard', 'x_i*(w,y) = ∂C/∂w_i', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR'], 'deriva coste respecto al precio del input → cuánto usas de cada input', 'adjetivo de intensidad de uso del input', 'bajo', 'alto', 'adjetivo de intensidad de uso del input', ARRAY['Asume diferenciabilidad — la función es suave','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de intensidad de uso del input.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de intensidad de uso del input.', '¿cuánto usas de cada input?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hotelling', 'y* = ∂π/∂p', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR'], 'deriva beneficio respecto al precio → cuánto produces', 'adjetivo de respuesta al precio', 'bajo', 'alto', 'adjetivo de respuesta al precio', ARRAY['Asume diferenciabilidad — la función es suave','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de respuesta al precio.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de respuesta al precio.', '¿cuánto produces?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ces', 'f = A[δK^ρ + (1-δ)L^ρ]^{1/ρ}', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR','TRANSFORMAR','ESCALAR'], 'transforma inputs por elasticidad ρ, escala por participación δ, acumula, transforma de vuelta, escala por productividad → producción con sustituibilidad constante', 'sujeto (output con flexibilidad paramétrica)', 'bajo valor', 'alto valor', 'sujeto (output con flexibilidad paramétrica)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (output con flexibilidad paramétrica).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿producción con sustituibilidad constante?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('pareto_eficiencia', '∄x'' t.q. u_i(x''_i) ≥ u_i(x_i) ∀i con ≥1 estricta', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara todas las asignaciones posibles, condiciona por mejora sin empeoramiento → no se puede mejorar a nadie sin perjudicar a otro', 'test de eficiencia (¿es óptimo?)', 'no significativo', 'significativo', 'test de eficiencia (¿es óptimo?)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de eficiencia (¿es óptimo?).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de eficiencia.', '¿no se puede mejorar a nadie sin perjudicar a otro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('precios_arrow_debreu', 'q(s) = β·π(s)·u''(c₁(s))/u''(c₀)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','ESCALAR','COMPONER'], 'deriva utilidades en dos estados, normaliza, escala por descuento, compone con probabilidad → precio de un seguro por estado del mundo', 'sujeto (precio del miedo a cada escenario)', 'bajo valor', 'alto valor', 'sujeto (precio del miedo a cada escenario)', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio del miedo a cada escenario).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿precio de un seguro por estado del mundo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equilibrio_bayesiano', 'σ_i*(θ_i) : E_{θ-i|θi}[u_i(σ*)] ≥ E[u_i(s_i,σ*_{-i})]', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','ACUMULAR','COMPARAR','SELECCIONAR'], 'condiciona por información privada, acumula utilidad esperada, compara estrategias, selecciona la mejor → jugar óptimo con información incompleta', 'prescripción bajo incertidumbre', 'no intervenir', 'intervenir fuerte', 'prescripción bajo incertidumbre', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción bajo incertidumbre.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción bajo incertidumbre.', '¿jugar óptimo con información incompleta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cournot', 'q_i* = (a-c_i-q_{-i})/(2b)', 'micro', ARRAY['PRESCRIBIR'], ARRAY['COMPARAR','COMPARAR','NORMALIZAR'], 'compara demanda con coste, compara con producción rival, normaliza → cuánto producir contra el competidor', 'prescripción de cantidad (oligopolio)', 'no intervenir', 'intervenir fuerte', 'prescripción de cantidad (oligopolio)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción de cantidad (oligopolio).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción de cantidad.', '¿cuánto producir contra el competidor?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bertrand', 'p* = c', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR'], 'compara precio con coste → la competencia en precios lleva al coste marginal', 'identidad (competencia perfecta en precios)', 'siempre se cumple', 'siempre se cumple', 'identidad (competencia perfecta en precios)', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad (competencia perfecta en precios).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad.', '¿la competencia en precios lleva al coste marginal?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('stackelberg', 'q_1* = argmax q_1·P(q_1+BR_2(q_1))-C_1', 'micro', ARRAY['PRESCRIBIR'], ARRAY['COMPONER','CONDICIONAR','SELECCIONAR'], 'compone precio×cantidad, condiciona por reacción del seguidor, selecciona máximo → ventaja del primero en mover', 'prescripción con compromiso (liderazgo)', 'no intervenir', 'intervenir fuerte', 'prescripción con compromiso (liderazgo)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción con compromiso (liderazgo).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción con compromiso.', '¿ventaja del primero en mover?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('folk_theorem', 'Todo pago factible+IR es SPE para δ suficientemente alto', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara payoff con punto de amenaza, condiciona por paciencia → la cooperación emerge si el futuro importa', 'condición (cuándo la cooperación es sostenible)', 'no se cumple', 'se cumple', 'condición (cuándo la cooperación es sostenible)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición (cuándo la cooperación es sostenible).', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición.', '¿la cooperación emerge si el futuro importa?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('incentive_compatibility', 'U(θ,θ) ≥ U(θ,θ̂) ∀θ,θ̂', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara utilidad de decir verdad vs mentir, condiciona por todo tipo → la verdad es óptima', 'restricción (cuándo conviene ser honesto)', 'no limita', 'limita severamente', 'restricción (cuándo conviene ser honesto)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''limita severamente''. restricción (cuándo conviene ser honesto).', 'Valor bajo → cerca del polo ''no limita''. Opuesto a restricción.', '¿la verdad es óptima?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('envelope_theorem', 'dU*/dθ = ∂v(q*(θ),θ)/∂θ', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','CONDICIONAR'], 'deriva utilidad óptima respecto al tipo, condicionado a decisión óptima → cómo cambia el valor cuando cambias quién eres', 'adjetivo de sensibilidad del valor al tipo', 'bajo', 'alto', 'adjetivo de sensibilidad del valor al tipo', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de sensibilidad del valor al tipo.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de sensibilidad del valor al tipo.', '¿cómo cambia el valor cuando cambias quién eres?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('moral_hazard', 'max E[x-w(x)] s.a. IC + IR', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','CONDICIONAR','SELECCIONAR'], 'condiciona por incentivos del agente, condiciona por participación, selecciona contrato → diseñar incentivos cuando no ves lo que hace el otro', 'prescripción (contrato óptimo bajo acción oculta)', 'no intervenir', 'intervenir fuerte', 'prescripción (contrato óptimo bajo acción oculta)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (contrato óptimo bajo acción oculta).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿diseñar incentivos cuando no ves lo que hace el otro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('señalizacion_spence', 'e*(θ_H) > e*(θ_L) t.q. w(e)-c(e,θ) satisface IC', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR','SELECCIONAR'], 'compara señales por tipo, condiciona por incentivos, selecciona separador → los buenos se distinguen invirtiendo más en señal', 'mecanismo (cómo demuestras lo que vales)', 'inactivo', 'activo', 'mecanismo (cómo demuestras lo que vales)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''activo''. mecanismo (cómo demuestras lo que vales).', 'Valor bajo → cerca del polo ''inactivo''. Opuesto a mecanismo.', '¿los buenos se distinguen invirtiendo más en señal?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('myerson_satterthwaite', 'No ∃ mecanismo IC+IR+eficiente+BB con tipos continuos', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'imposibilidad — no puedes tener incentivos, participación, eficiencia y presupuesto equilibrado a la vez', 'imposibilidad (el mercado perfecto no existe bajo asimetría)', 'imposible', 'imposible', 'imposibilidad (el mercado perfecto no existe bajo ', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Esta fórmula es un resultado teórico/imposibilidad", "operacion": "No requiere cálculo", "produce": "PROPIEDAD del sistema"}]'::jsonb, 'Valor alto → cerca del polo ''imposible''. imposibilidad (el mercado perfecto no existe bajo asimetría).', 'Valor bajo → cerca del polo ''imposible''. Opuesto a imposibilidad.', '¿imposibilidad (el mercado perfecto no existe bajo asimetría)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('romer_variedades', 'Y = L^(1-α)∫₀^A x(i)^α di; Ȧ = δ·L_A·A', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','INTEGRAR','COMPONER','DERIVAR','COMPONER'], 'transforma por elasticidad, integra sobre variedades, compone trabajo×capital; la innovación es más gente investigando × más conocimiento', 'sistema (crecimiento por crear cosas nuevas)', 'simple', 'complejo', 'sistema (crecimiento por crear cosas nuevas)', ARRAY['Asume diferenciabilidad — la función es suave','Asume integrabilidad — la función está bien definida','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema (crecimiento por crear cosas nuevas).', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema.', '¿sistema (crecimiento por crear cosas nuevas)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('schumpeter_destruccion_creativa', 'V = π/(r+φ) donde φ = tasa destrucción', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','ACUMULAR','INVERTIR'], 'normaliza beneficio del monopolio temporal, acumula con riesgo de destrucción, invierte → valor de innovar sabiendo que te reemplazarán', 'sujeto (precio de la innovación con fecha de caducidad)', 'bajo valor', 'alto valor', 'sujeto (precio de la innovación con fecha de caduc', ARRAY['Asume invertibilidad — la función tiene inversa','La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio de la innovación con fecha de caducidad).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿valor de innovar sabiendo que te reemplazarán?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('mankiw_romer_weil', 'ln(Y/L) = const + [α/(1-α)]ln(s_K) + [β/(1-α)]ln(s_H) - [(α+β)/(1-α)]ln(n+g+δ)', 'macro', ARRAY['DESCOMPONER'], ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR'], 'transforma a logaritmos, escala por elasticidades, acumula → renta per cápita explicada por ahorro físico, humano y crecimiento poblacional', 'descomposición (por qué unos países son ricos y otros pobres)', 'un solo factor', 'múltiples factores', 'descomposición (por qué unos países son ricos y ot', ARRAY['Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición (por qué unos países son ricos y otros pobres).', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición.', '¿renta per cápita explicada por ahorro físico, humano y crecimiento pob?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('contabilidad_crecimiento', 'ΔA/A = ΔY/Y - α·ΔK/K - (1-α)·ΔL/L', 'macro', ARRAY['DESCOMPONER'], ARRAY['COMPARAR','ESCALAR','COMPARAR','ESCALAR','COMPARAR'], 'compara crecimiento del output con contribución ponderada de capital y trabajo → lo que sobra es productividad', 'residuo (la medida de nuestra ignorancia — Solow)', 'todo explicado', 'mucho sin explicar', 'residuo (la medida de nuestra ignorancia — Solow)', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''mucho sin explicar''. residuo (la medida de nuestra ignorancia — Solow).', 'Valor bajo → cerca del polo ''todo explicado''. Opuesto a residuo.', '¿lo que sobra es productividad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('transversalidad', 'lim_{t→∞} β^t·u''(c_t)·k_t = 0', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','DERIVAR','COMPONER','SELECCIONAR'], 'escala por descuento, deriva utilidad marginal, compone con capital, selecciona límite → no acumules para siempre ni te arruines', 'restricción (la vida es finita — no mueras rico ni pobre)', 'no limita', 'limita severamente', 'restricción (la vida es finita — no mueras rico ni', ARRAY['Asume que el óptimo existe y es alcanzable','Asume diferenciabilidad — la función es suave','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''limita severamente''. restricción (la vida es finita — no mueras rico ni pobre).', 'Valor bajo → cerca del polo ''no limita''. Opuesto a restricción.', '¿no acumules para siempre ni te arruines?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('blanchard_kahn', 'condición: #eigenvalues>1 = #variables forward', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','COMPARAR'], 'transforma sistema a eigenvalores, compara número de inestables con variables forward → ¿el modelo tiene solución única?', 'test de determinación (¿este modelo está bien definido?)', 'no significativo', 'significativo', 'test de determinación (¿este modelo está bien defi', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de determinación (¿este modelo está bien definido?).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de determinación.', '¿¿el modelo tiene solución única??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('perdida_banco_central', 'L = E Σ β^t [(π-π*)² + λ·x²]', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','COMPARAR','TRANSFORMAR','ESCALAR','ACUMULAR','ESCALAR','CONDICIONAR'], 'compara inflación con objetivo (al cuadrado), compara output gap (al cuadrado), escala por preferencia λ, acumula en el tiempo, escala por descuento → cuánto sufre el banco central', 'sujeto (dolor del banquero central)', 'bajo valor', 'alto valor', 'sujeto (dolor del banquero central)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (dolor del banquero central).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿cuánto sufre el banco central?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('inconsistencia_temporal', 'π^e = π* + λκ/α > π* (sesgo inflacionario)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR','ACUMULAR'], 'compara equilibrio con objetivo, normaliza por parámetros, acumula sesgo → sin compromiso creíble, siempre hay más inflación de la deseada', 'adjetivo de credibilidad (cuánto vale tu palabra)', 'bajo', 'alto', 'adjetivo de credibilidad (cuánto vale tu palabra)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de credibilidad (cuánto vale tu palabra).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de credibilidad.', '¿sin compromiso creíble, siempre hay más inflación de la deseada?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gauss_markov', 'β̂_OLS es BLUE bajo E[ε|X]=0, Var(ε|X)=σ²I', 'econometria', ARRAY['VERIFICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona por supuestos clásicos, compara con todo estimador lineal insesgado → OLS es el mejor (bajo esos supuestos)', 'garantía (OLS gana si el mundo es como asumes)', 'no cumple', 'garantizado', 'garantía (OLS gana si el mundo es como asumes)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía (OLS gana si el mundo es como asumes).', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía.', '¿OLS es el mejor (bajo esos supuestos)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('varianza_robusta_white', 'V̂ = (X''X)⁻¹(Σ ê²xᵢxᵢ'')(X''X)⁻¹', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','TRANSFORMAR','COMPONER','COMPONER','INVERTIR'], 'invierte la varianza de X, transforma residuos al cuadrado, compone sandwich → incertidumbre correcta aunque los errores sean irregulares', 'herramienta (errores estándar que no mienten)', 'no aplica', 'muy útil', 'herramienta (errores estándar que no mienten)', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (errores estándar que no mienten).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿incertidumbre correcta aunque los errores sean irregulares?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lr_test', 'LR = 2[ℓ(θ̂_u) - ℓ(θ̂_r)]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','ESCALAR'], 'compara verosimilitud del modelo libre vs restringido, escala por 2 → ¿las restricciones duelen?', 'test (¿la simplificación pierde información?)', 'no significativo', 'significativo', 'test (¿la simplificación pierde información?)', ARRAY['La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test (¿la simplificación pierde información?).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test.', '¿¿las restricciones duelen??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('wald_test', 'W = (Rθ̂-r)''[RVR'']⁻¹(Rθ̂-r)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPONER','INVERTIR','COMPONER'], 'compara estimaciones con restricción, compone con varianza invertida → distancia cuadrática a la hipótesis', 'test (cuán lejos estás de lo que asumes)', 'no significativo', 'significativo', 'test (cuán lejos estás de lo que asumes)', ARRAY['Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test (cuán lejos estás de lo que asumes).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test.', '¿distancia cuadrática a la hipótesis?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('aic', 'AIC = -2ℓ(θ̂) + 2k', 'econometria', ARRAY['COMPARAR'], ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR'], 'transforma verosimilitud (×-2), escala parámetros (×2), acumula → calidad penalizada por complejidad', 'score (cuánto vale tu modelo descontando cuánto le cuesta)', 'mal modelo', 'buen modelo', 'score (cuánto vale tu modelo descontando cuánto le', ARRAY['Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''buen modelo''. score (cuánto vale tu modelo descontando cuánto le cuesta).', 'Valor bajo → cerca del polo ''mal modelo''. Opuesto a score.', '¿calidad penalizada por complejidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('probit', 'P(y=1|x) = Φ(x''β)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','TRANSFORMAR'], 'compone variables×coeficientes, transforma por función normal acumulada → probabilidad de que ocurra', 'adjetivo de probabilidad (cuán probable es el evento)', 'bajo', 'alto', 'adjetivo de probabilidad (cuán probable es el even', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de probabilidad (cuán probable es el evento).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de probabilidad.', '¿probabilidad de que ocurra?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('logit', 'P(y=1|x) = exp(x''β)/(1+exp(x''β))', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','TRANSFORMAR','NORMALIZAR'], 'compone variables×coeficientes, transforma a exponencial, normaliza → probabilidad logística', 'adjetivo de probabilidad (versión logística)', 'bajo', 'alto', 'adjetivo de probabilidad (versión logística)', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de probabilidad (versión logística).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de probabilidad.', '¿probabilidad logística?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tobit', 'y* = x''β+ε; y = max(0,y*)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACOTAR'], 'compone variables×coeficientes, acota por cero → estimar cuando los datos están censurados', 'herramienta (ver lo que está detrás del cero)', 'no aplica', 'muy útil', 'herramienta (ver lo que está detrás del cero)', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: poner límites", "operacion": "max(0,x) o clamp", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (ver lo que está detrás del cero).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿estimar cuando los datos están censurados?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bootstrap', 'θ̂* = g(X₁*,...,Xₙ*) remuestreando con reemplazo', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ACUMULAR','NORMALIZAR'], 'transforma por remuestreo aleatorio, acumula estadísticos, normaliza → incertidumbre sin supuestos distribucionales', 'herramienta (medir error sin asumir nada)', 'no aplica', 'muy útil', 'herramienta (medir error sin asumir nada)', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (medir error sin asumir nada).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿incertidumbre sin supuestos distribucionales?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kaplan_meier', 'Ŝ(t) = Π (1-d_i/n_i)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','COMPONER'], 'normaliza eventos por expuestos, compone probabilidades de supervivencia → probabilidad de seguir vivo/activo', 'adjetivo de supervivencia', 'bajo', 'alto', 'adjetivo de supervivencia', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de supervivencia.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de supervivencia.', '¿probabilidad de seguir vivo/activo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('chebyshev', 'P(|X-μ| ≥ kσ) ≤ 1/k²', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR','TRANSFORMAR','INVERTIR'], 'compara con media, normaliza por desviación, transforma al cuadrado, invierte → cota universal de cuán raro es un evento', 'cota (lo peor que puede pasar sin asumir nada)', 'cota laxa', 'cota ajustada', 'cota (lo peor que puede pasar sin asumir nada)', ARRAY['Asume invertibilidad — la función tiene inversa','La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''cota ajustada''. cota (lo peor que puede pasar sin asumir nada).', 'Valor bajo → cerca del polo ''cota laxa''. Opuesto a cota.', '¿cota universal de cuán raro es un evento?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('delta_method', '√n(g(θ̂)-g(θ)) →d N(0, g''V g'')', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','TRANSFORMAR'], 'deriva la función, compone con varianza del estimador, transforma → incertidumbre de funciones de estimadores', 'herramienta (propagar incertidumbre a través de funciones)', 'no aplica', 'muy útil', 'herramienta (propagar incertidumbre a través de fu', ARRAY['Asume diferenciabilidad — la función es suave','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (propagar incertidumbre a través de funciones).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿incertidumbre de funciones de estimadores?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('radon_nikodym', 'dQ/dP = f → Q(A) = ∫_A f dP', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','INTEGRAR'], 'normaliza una medida por otra, integra → cambiar de perspectiva probabilística', 'herramienta universal (ver el mundo desde otra distribución)', 'no aplica', 'muy útil', 'herramienta universal (ver el mundo desde otra dis', ARRAY['Asume integrabilidad — la función está bien definida','La normalización asume que el denominador es significativo','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta universal (ver el mundo desde otra distribución).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta universal.', '¿cambiar de perspectiva probabilística?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('girsanov', 'dQ/dP = exp(-∫θdW - ½∫θ²dt)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INTEGRAR','TRANSFORMAR','NORMALIZAR'], 'compone drift×browniano, integra, transforma a exponencial, normaliza → cambiar drift preservando estructura estocástica', 'herramienta (pricing neutral al riesgo — la base de toda finanza moderna)', 'no aplica', 'muy útil', 'herramienta (pricing neutral al riesgo — la base d', ARRAY['Asume integrabilidad — la función está bien definida','La normalización asume que el denominador es significativo','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (pricing neutral al riesgo — la base de toda finanza moderna).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿cambiar drift preservando estructura estocástica?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('martingala', 'E[X_{t+1}|F_t] = X_t', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona por información actual, compara esperanza futura con presente → sin tendencia predecible', 'propiedad (el futuro es justo dado lo que sabes)', 'no tiene', 'tiene fuerte', 'propiedad (el futuro es justo dado lo que sabes)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''tiene fuerte''. propiedad (el futuro es justo dado lo que sabes).', 'Valor bajo → cerca del polo ''no tiene''. Opuesto a propiedad.', '¿sin tendencia predecible?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('quasi_hiperbolic', 'U₀ = u₀ + β·Σδ^t·u_t (β<1)', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ESCALAR','TRANSFORMAR','ACUMULAR'], 'escala presente por 1, escala futuro por β<1 (penalización), transforma por descuento δ^t, acumula → presente vale desproporcionadamente más', 'adjetivo de sesgo presente (la procrastinación modelada)', 'bajo', 'alto', 'adjetivo de sesgo presente (la procrastinación mod', ARRAY['Agentes con racionalidad limitada o sesgos'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de sesgo presente (la procrastinación modelada).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de sesgo presente.', '¿presente vale desproporcionadamente más?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('aversion_inequidad_fehr_schmidt_simple', 'U = x_i - α·max(x_j-x_i,0) - β·max(x_i-x_j,0)', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','ACOTAR','ESCALAR','COMPARAR','ACOTAR','ESCALAR','COMPARAR'], 'compara con otros (envidia si menos, culpa si más), acota a positivo, escala por intensidad → utilidad que sufre por desigualdad', 'adjetivo de justicia percibida', 'bajo', 'alto', 'adjetivo de justicia percibida', ARRAY['La comparación asume que las escalas son compatibles','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Poner límites", "operacion": "max(0,x) o clamp", "produce": "ACOTADO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Poner límites", "operacion": "max(0,x) o clamp", "produce": "ACOTADO"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de justicia percibida.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de justicia percibida.', '¿utilidad que sufre por desigualdad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('referencia_dependiente_koszegi_rabin', 'U(c|r) = m(c) + μ(m(c)-m(r))', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR'], 'compara consumo real con expectativa (referencia), transforma la diferencia por aversión a pérdida, acumula → cuánto duele no cumplir tus expectativas', 'adjetivo de decepción/satisfacción relativa', 'bajo', 'alto', 'adjetivo de decepción/satisfacción relativa', ARRAY['La comparación asume que las escalas son compatibles','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de decepción/satisfacción relativa.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de decepción/satisfacción relativa.', '¿cuánto duele no cumplir tus expectativas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('maxmin_ambiguedad', 'V(f) = min_{P∈C} E_P[u(f)]', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','ACUMULAR','SELECCIONAR'], 'condiciona por múltiples distribuciones posibles, acumula utilidad esperada bajo cada una, selecciona la peor → decisión cuando no sabes ni las probabilidades', 'prescripción bajo ignorancia profunda', 'no intervenir', 'intervenir fuerte', 'prescripción bajo ignorancia profunda', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción bajo ignorancia profunda.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción bajo ignorancia profunda.', '¿decisión cuando no sabes ni las probabilidades?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('demanda_hicksiana', 'h(p,ū)=argmin p·x s.a. u(x)≥ū', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','SELECCIONAR'], 'demanda aislando efecto sustitución', 'demanda compensada', 'bajo', 'alto', 'demanda compensada', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. demanda compensada.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a demanda compensada.', '¿demanda compensada?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('variacion_compensatoria_integral', 'CV=∫p¹_p⁰ h(p,u⁰)dp', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['INTEGRAR'], 'integra demanda hicksiana entre precios → coste exacto del cambio', 'medida exacta de bienestar', 'bajo bienestar', 'alto bienestar', 'medida exacta de bienestar', ARRAY['Asume integrabilidad — la función está bien definida','Agentes racionales que maximizan utilidad'], '[{"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto bienestar''. medida exacta de bienestar.', 'Valor bajo → cerca del polo ''bajo bienestar''. Opuesto a medida exacta de bienestar.', '¿coste exacto del cambio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('utilidad_esperada_vnm', 'U(L)=Σp_i·u(x_i)', 'micro', ARRAY['VALORAR'], ARRAY['COMPONER','ACUMULAR'], 'compone probabilidad×utilidad, acumula → valor esperado de la lotería', 'sujeto (valor de la incertidumbre)', 'bajo valor', 'alto valor', 'sujeto (valor de la incertidumbre)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (valor de la incertidumbre).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿valor esperado de la lotería?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('aversion_relativa_riesgo', 'r_R=-x·u''''/u''', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','COMPONER','TRANSFORMAR'], 'como Arrow-Pratt pero escalada por riqueza → aversión relativa', 'adjetivo de aversión proporcional', 'bajo', 'alto', 'adjetivo de aversión proporcional', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de aversión proporcional.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de aversión proporcional.', '¿aversión relativa?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('dominancia_estocastica_2', 'F≥_SSD G ⟺ ∫[G(x)-F(x)]dx≥0', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','INTEGRAR'], 'compara distribuciones acumuladas, integra → preferida por todos los aversos al riesgo', 'ordenamiento (para cualquier averso)', 'inferior', 'superior', 'ordenamiento (para cualquier averso)', ARRAY['Asume integrabilidad — la función está bien definida','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''superior''. ordenamiento (para cualquier averso).', 'Valor bajo → cerca del polo ''inferior''. Opuesto a ordenamiento.', '¿preferida por todos los aversos al riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('utilidad_crra', 'u(c)=c^(1-γ)/(1-γ)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','NORMALIZAR'], 'transforma consumo por potencia, normaliza → aversión constante relativa', 'función paramétrica de preferencias', 'bajo', 'alto', 'función paramétrica de preferencias', ARRAY['La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. función paramétrica de preferencias.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a función paramétrica de preferencias.', '¿aversión constante relativa?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('utilidad_cara', 'u(c)=-(1/α)e^(-αc)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','TRANSFORMAR','TRANSFORMAR'], 'escala consumo, transforma exponencial, invierte → aversión constante absoluta', 'función paramétrica de preferencias', 'bajo', 'alto', 'función paramétrica de preferencias', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. función paramétrica de preferencias.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a función paramétrica de preferencias.', '¿aversión constante absoluta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('restriccion_presup_intertemporal', 'Σc_t/(1+r)^t = Σy_t/(1+r)^t + a_0', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','INVERTIR','TRANSFORMAR','ACUMULAR','COMPARAR'], 'descuenta consumo y renta, acumula, compara → el VP de lo que gastas = VP de lo que ganas', 'identidad intertemporal', 'siempre se cumple', 'siempre se cumple', 'identidad intertemporal', ARRAY['Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad intertemporal.', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad intertemporal.', '¿el VP de lo que gastas = VP de lo que ganas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('rendimientos_escala_formal', 'f(tx)=t^α·f(x)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','TRANSFORMAR','COMPARAR'], 'escala todos los inputs, transforma por homogeneidad, compara → ¿más que proporcional?', 'test de escala', 'no significativo', 'significativo', 'test de escala', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de escala.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de escala.', '¿¿más que proporcional??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('funcion_beneficio', 'π(p,w)=max p·f(x)-w·x', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPONER','COMPARAR','SELECCIONAR'], 'compone ingreso, compone coste, compara, selecciona máximo → beneficio máximo posible', 'sujeto (techo de ganancia)', 'bajo valor', 'alto valor', 'sujeto (techo de ganancia)', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (techo de ganancia).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿beneficio máximo posible?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('translog', 'lnC=α₀+Σα_i·lnw_i+½ΣΣγ_ij·lnw_i·lnw_j+β·lny', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ESCALAR','COMPONER','ACUMULAR'], 'transforma a log, escala por parámetros, compone pares, acumula → flexibilidad máxima en costes', 'aproximación flexible (no asume forma funcional)', 'bajo', 'alto', 'aproximación flexible (no asume forma funcional)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. aproximación flexible (no asume forma funcional).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a aproximación flexible.', '¿flexibilidad máxima en costes?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equilibrio_con_produccion', 'Σx_i = Σω_i + Σy_j', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','ACUMULAR','ACUMULAR','COMPARAR'], 'acumula demandas, acumula dotaciones, acumula producción, compara → equilibrio con empresas', 'sistema de equilibrio extendido', 'simple', 'complejo', 'sistema de equilibrio extendido', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema de equilibrio extendido.', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema de equilibrio extendido.', '¿equilibrio con empresas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('nucleo_economia', 'Core(E): ∄ coalición S que bloquea', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara asignaciones posibles por coalición, condiciona por bloqueo → nadie puede mejorar agrupándose', 'estabilidad (la asignación es inamovible)', 'bajo', 'alto', 'estabilidad (la asignación es inamovible)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. estabilidad (la asignación es inamovible).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a estabilidad.', '¿nadie puede mejorar agrupándose?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('subasta_primer_precio', 'b(v)=v-∫₀ᵛ[F(t)/F(v)]^(n-1)dt', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','INTEGRAR','COMPARAR'], 'normaliza distribución, transforma por competidores, integra, compara con valor → cuánto menos pujas', 'prescripción (cuánto esconder de tu valor)', 'no intervenir', 'intervenir fuerte', 'prescripción (cuánto esconder de tu valor)', ARRAY['Asume integrabilidad — la función está bien definida','La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (cuánto esconder de tu valor).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿cuánto menos pujas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('revenue_equivalence', 'E[Rev] igual en todas las subastas estándar', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona por simetría+IPV, compara mecanismos → todos recaudan igual', 'equivalencia (la forma no importa, solo la estructura)', 'diferentes', 'equivalentes', 'equivalencia (la forma no importa, solo la estruct', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''equivalentes''. equivalencia (la forma no importa, solo la estructura).', 'Valor bajo → cerca del polo ''diferentes''. Opuesto a equivalencia.', '¿todos recaudan igual?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bienestar_nash', 'W=Π u_i (o Σ ln u_i)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ACUMULAR'], 'transforma a logaritmo, acumula → bienestar con aversión moderada a desigualdad', 'sujeto (bienestar con equidad implícita)', 'bajo valor', 'alto valor', 'sujeto (bienestar con equidad implícita)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (bienestar con equidad implícita).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿bienestar con aversión moderada a desigualdad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('arrow_imposibilidad', 'No ∃ f:L^n→L con U+P+IIA+ND', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'imposibilidad — no hay regla perfecta para agregar preferencias', 'imposibilidad (la democracia perfecta no existe)', 'imposible', 'imposible', 'imposibilidad (la democracia perfecta no existe)', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Esta fórmula es un resultado teórico/imposibilidad", "operacion": "No requiere cálculo", "produce": "PROPIEDAD del sistema"}]'::jsonb, 'Valor alto → cerca del polo ''imposible''. imposibilidad (la democracia perfecta no existe).', 'Valor bajo → cerca del polo ''imposible''. Opuesto a imposibilidad.', '¿imposibilidad (la democracia perfecta no existe)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gibbard_satterthwaite', 'Todo mecanismo no-dictatorial con ≥3 alternativas es manipulable', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'imposibilidad — siempre puedes mentir para ganar', 'imposibilidad (la honestidad no se puede forzar sin dictadura)', 'imposible', 'imposible', 'imposibilidad (la honestidad no se puede forzar si', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Esta fórmula es un resultado teórico/imposibilidad", "operacion": "No requiere cálculo", "produce": "PROPIEDAD del sistema"}]'::jsonb, 'Valor alto → cerca del polo ''imposible''. imposibilidad (la honestidad no se puede forzar sin dictadura).', 'Valor bajo → cerca del polo ''imposible''. Opuesto a imposibilidad.', '¿imposibilidad (la honestidad no se puede forzar sin dictadura)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('convergencia_condicional', 'lny(t)-lny(0)=(1-e^(-λt))[lny*-lny(0)]', 'macro', ARRAY['PREDECIR'], ARRAY['COMPARAR','TRANSFORMAR','COMPONER'], 'compara con estado estacionario, transforma exponencial, compone → velocidad de convergencia', 'adjetivo de velocidad hacia el equilibrio', 'bajo', 'alto', 'adjetivo de velocidad hacia el equilibrio', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de velocidad hacia el equilibrio.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de velocidad hacia el equilibrio.', '¿velocidad de convergencia?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('rbc_basico', 'max E₀Σβ^t u(c,1-l) s.a. k''=Af(k,l)+(1-δ)k-c', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ACUMULAR','CONDICIONAR','SELECCIONAR'], 'escala por descuento, acumula utilidad esperada, condiciona por acumulación de capital, selecciona máximo → ciclos por shocks tecnológicos', 'sistema (fluctuaciones sin fallos de mercado)', 'simple', 'complejo', 'sistema (fluctuaciones sin fallos de mercado)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema (fluctuaciones sin fallos de mercado).', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema.', '¿ciclos por shocks tecnológicos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('euler_estocastica', 'u''(c_t)=β·E_t[(1+r)u''(c_{t+1})]', 'macro', ARRAY['PREDECIR'], ARRAY['DERIVAR','ESCALAR','CONDICIONAR','DERIVAR','COMPARAR'], 'deriva utilidad hoy, escala por descuento, condiciona por futuro, deriva utilidad mañana, compara → suavizado óptimo bajo incertidumbre', 'condición de optimalidad intertemporal', 'no se cumple', 'se cumple', 'condición de optimalidad intertemporal', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición de optimalidad intertemporal.', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición de optimalidad intertemporal.', '¿suavizado óptimo bajo incertidumbre?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('calvo_parametro', 'κ=(1-θ)(1-βθ)/θ', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPONER','NORMALIZAR'], 'compara rigidez, compone con descuento, normaliza → pendiente de la NKPC', 'parámetro (cuánta inflación genera un punto de gap)', 'bajo', 'alto', 'parámetro (cuánta inflación genera un punto de gap', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. parámetro (cuánta inflación genera un punto de gap).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a parámetro.', '¿pendiente de la NKPC?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('baumol_tobin', 'M*/P=(Y·c/(2i))^(1/2)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','NORMALIZAR','TRANSFORMAR'], 'compone renta×coste transacción, normaliza por tipo de interés, transforma raíz → demanda de dinero por motivo transacción', 'sujeto (cuánto dinero quieres tener en el bolsillo)', 'bajo valor', 'alto valor', 'sujeto (cuánto dinero quieres tener en el bolsillo', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (cuánto dinero quieres tener en el bolsillo).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿demanda de dinero por motivo transacción?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regla_friedman', 'i*=0', 'macro', ARRAY['PRESCRIBIR','OPTIMIZAR'], ARRAY['SELECCIONAR'], 'selecciona tipo nominal cero → coste de oportunidad del dinero = 0', 'prescripción (el tipo óptimo es cero)', 'no intervenir', 'intervenir fuerte', 'prescripción (el tipo óptimo es cero)', ARRAY['Asume que el óptimo existe y es alcanzable','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (el tipo óptimo es cero).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿coste de oportunidad del dinero = 0?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ecuacion_cuantitativa', 'MV=PY', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPONER','COMPARAR'], 'compone dinero×velocidad, compone precios×output, compara → identidad monetaria', 'identidad contable (siempre se cumple por definición)', 'siempre se cumple', 'siempre se cumple', 'identidad contable (siempre se cumple por definici', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''siempre se cumple''. identidad contable (siempre se cumple por definición).', 'Valor bajo → cerca del polo ''siempre se cumple''. Opuesto a identidad contable.', '¿identidad monetaria?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('suavizado_impositivo', 'τ_t=τ*=r·B₀+E[G]/Y ∀t', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR','NORMALIZAR'], 'compone tipo×deuda, acumula gasto esperado, normaliza por PIB → tipo constante óptimo', 'prescripción fiscal (no cambies los impuestos)', 'no intervenir', 'intervenir fuerte', 'prescripción fiscal (no cambies los impuestos)', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción fiscal (no cambies los impuestos).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción fiscal.', '¿tipo constante óptimo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('no_ponzi', 'lim B_T/(1+r)^T=0', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','TRANSFORMAR','SELECCIONAR'], 'normaliza deuda por factor de descuento, transforma al infinito, selecciona límite → no puedes endeudarte para siempre', 'restricción (la deuda no explota)', 'no limita', 'limita severamente', 'restricción (la deuda no explota)', ARRAY['Asume que el óptimo existe y es alcanzable','La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''limita severamente''. restricción (la deuda no explota).', 'Valor bajo → cerca del polo ''no limita''. Opuesto a restricción.', '¿no puedes endeudarte para siempre?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('condicion_marshall_lerner', '|ε_X|+|ε_M|>1', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','COMPARAR'], 'acumula elasticidades de export+import, compara con 1 → ¿funciona devaluar?', 'test (¿la devaluación mejora la balanza comercial?)', 'no significativo', 'significativo', 'test (¿la devaluación mejora la balanza comercial?', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test (¿la devaluación mejora la balanza comercial?).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test.', '¿¿funciona devaluar??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('heckscher_ohlin', 'País K-abundante exporta bienes K-intensivos', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara dotaciones relativas de factores, condiciona por intensidad → por qué cada país exporta lo que exporta', 'predicción de patrón comercial', 'bajo', 'alto', 'predicción de patrón comercial', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. predicción de patrón comercial.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a predicción de patrón comercial.', '¿por qué cada país exporta lo que exporta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('mundell_fleming', 'IS-LM abierto: Y=C+I+G+NX(e); M/P=L(Y,i); i=i*', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','COMPARAR','COMPARAR'], 'acumula componentes de demanda, compara dinero con demanda, compara tipo con exterior → ¿funciona la política fiscal/monetaria con tipo de cambio fijo/flexible?', 'sistema (efectividad de políticas en economía abierta)', 'simple', 'complejo', 'sistema (efectividad de políticas en economía abie', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema (efectividad de políticas en economía abierta).', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema.', '¿¿funciona la política fiscal/monetaria con tipo de cambio fijo/flexibl?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tipo_cambio_ppc_formal', 'E=P/P*', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR'], 'normaliza nivel de precios por nivel extranjero → tipo de cambio de equilibrio', 'sujeto (precio relativo entre países)', 'bajo valor', 'alto valor', 'sujeto (precio relativo entre países)', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio relativo entre países).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿tipo de cambio de equilibrio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('paridad_intereses_descubierta', 'E_t[e_{t+1}]-e_t = i-i*', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPARAR'], 'compara tipo de cambio esperado con actual, compara tipos de interés → depreciación esperada = diferencial de tipos', 'condición de arbitraje internacional', 'no se cumple', 'se cumple', 'condición de arbitraje internacional', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición de arbitraje internacional.', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición de arbitraje internacional.', '¿depreciación esperada = diferencial de tipos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('krugman_nueva_geo', 'W=Σ T^(1-σ)YE/P^(1-σ)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','COMPONER','ACUMULAR','NORMALIZAR'], 'transforma costes transporte, compone con mercado, acumula sobre regiones, normaliza → por qué las fábricas se concentran', 'explicación de aglomeración geográfica', 'no explica', 'explica completamente', 'explicación de aglomeración geográfica', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''explica completamente''. explicación de aglomeración geográfica.', 'Valor bajo → cerca del polo ''no explica''. Opuesto a explicación de aglomeración geográfica.', '¿por qué las fábricas se concentran?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('melitz_exportadores', 'Exporta si φ≥φ_X*', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara productividad con umbral, condiciona por costes fijos de exportar → solo las mejores empresas exportan', 'selección (quién exporta y quién no)', 'no selecciona', 'selecciona claramente', 'selección (quién exporta y quién no)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''selecciona claramente''. selección (quién exporta y quién no).', 'Valor bajo → cerca del polo ''no selecciona''. Opuesto a selección.', '¿solo las mejores empresas exportan?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ccapm', 'E[R_i]-r_f = γ·Cov(R_i,Δc/c)', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPONER','NORMALIZAR'], 'compara retorno con tasa libre, compone covarianza con consumo, normaliza → prima por riesgo de consumo', 'prescripción (cuánto debe rendir un activo según cuándo pierdes)', 'no intervenir', 'intervenir fuerte', 'prescripción (cuánto debe rendir un activo según c', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción (cuánto debe rendir un activo según cuándo pierdes).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción.', '¿prima por riesgo de consumo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('vasicek', 'dr=a(b-r)dt+σdW', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','ESCALAR','ACUMULAR','COMPONER'], 'compara tipo con media, escala por velocidad, acumula drift, compone con difusión → tipo de interés que vuelve a la media', 'proceso (dinámica mean-reverting)', 'estático', 'dinámico', 'proceso (dinámica mean-reverting)', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso (dinámica mean-reverting).', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso.', '¿tipo de interés que vuelve a la media?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('frontera_varianza_minima', 'min w''Σw s.a. w''μ=μ̄, w''1=1', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','CONDICIONAR','SELECCIONAR'], 'compone pesos×covarianza, condiciona por retorno objetivo, selecciona mínimo riesgo → portfolio óptimo', 'prescripción de cartera', 'no intervenir', 'intervenir fuerte', 'prescripción de cartera', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción de cartera.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción de cartera.', '¿portfolio óptimo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('neutralidad_riesgo', 'p=e^(-rT)·E^Q[X_T]', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','INVERTIR','TRANSFORMAR','CONDICIONAR','ACUMULAR'], 'escala por tipo libre, invierte exponencial, transforma a medida Q, condiciona por info, acumula → precio bajo mundo neutral', 'herramienta de valoración universal', 'no aplica', 'muy útil', 'herramienta de valoración universal', ARRAY['Asume que las condiciones son observables y verificables','Asume invertibilidad — la función tiene inversa','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de valoración universal.', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de valoración universal.', '¿precio bajo mundo neutral?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hansen_jagannathan', '|E[R_e]-r_f|/σ(R_e) ≤ σ(m)/E[m]', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR','NORMALIZAR','COMPARAR'], 'normaliza prima por volatilidad, normaliza SDF, compara ambos ratios → cota de lo que puede rendir un activo', 'restricción (límite de la eficiencia)', 'no limita', 'limita severamente', 'restricción (límite de la eficiencia)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''limita severamente''. restricción (límite de la eficiencia).', 'Valor bajo → cerca del polo ''no limita''. Opuesto a restricción.', '¿cota de lo que puede rendir un activo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('browniano_geometrico', 'dS/S=μdt+σdW', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','ACUMULAR','COMPONER'], 'normaliza cambio por nivel, acumula drift, compone con difusión → dinámica de cualquier activo', 'proceso fundamental de finanzas', 'estático', 'dinámico', 'proceso fundamental de finanzas', ARRAY['La normalización asume que el denominador es significativo','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso fundamental de finanzas.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso fundamental de finanzas.', '¿dinámica de cualquier activo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gls', 'β̂_GLS=(X''Ω⁻¹X)⁻¹X''Ω⁻¹y', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','COMPONER','INVERTIR','COMPONER'], 'como OLS pero ponderando por estructura de errores → eficiente con errores irregulares', 'estimación eficiente', 'imprecisa', 'precisa', 'estimación eficiente', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación eficiente.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación eficiente.', '¿eficiente con errores irregulares?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('varianza_clustered', 'V̂=...sandwich por clusters', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','COMPONER','COMPONER','INVERTIR'], 'sandwich con agrupación por clusters → errores correctos cuando hay correlación dentro de grupos', 'herramienta (no subestimar incertidumbre)', 'no aplica', 'muy útil', 'herramienta (no subestimar incertidumbre)', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (no subestimar incertidumbre).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿errores correctos cuando hay correlación dentro de grupos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('informacion_fisher', 'I(θ)=-E[∂²ℓ/∂θ²]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','CONDICIONAR','TRANSFORMAR'], 'deriva dos veces log-verosimilitud, esperanza, invierte signo → cuánta información tienen los datos sobre θ', 'sujeto (riqueza informativa de los datos)', 'bajo valor', 'alto valor', 'sujeto (riqueza informativa de los datos)', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (riqueza informativa de los datos).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿cuánta información tienen los datos sobre θ?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cramer_rao', 'Var(θ̂)≥I(θ)⁻¹', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['INVERTIR','COMPARAR'], 'invierte información, compara con varianza → mínima incertidumbre posible', 'cota inferior (lo mejor que puedes lograr)', 'cota laxa', 'cota ajustada', 'cota inferior (lo mejor que puedes lograr)', ARRAY['Asume invertibilidad — la función tiene inversa','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''cota ajustada''. cota inferior (lo mejor que puedes lograr).', 'Valor bajo → cerca del polo ''cota laxa''. Opuesto a cota inferior.', '¿mínima incertidumbre posible?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lm_score_test', 'LM=s''I⁻¹s', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','COMPONER'], 'compone score×info_inversa×score → test desde modelo restringido', 'test sin necesidad de estimar el modelo completo', 'no significativo', 'significativo', 'test sin necesidad de estimar el modelo completo', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test sin necesidad de estimar el modelo completo.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test sin necesidad de estimar el modelo completo.', '¿test desde modelo restringido?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bic', 'BIC=-2ℓ+k·ln(n)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ESCALAR','COMPONER','ACUMULAR'], 'transforma verosimilitud, escala parámetros por log(n), compone penalización, acumula → más estricto que AIC', 'score de selección de modelo (más parsimonioso)', 'mal modelo', 'buen modelo', 'score de selección de modelo (más parsimonioso)', ARRAY['Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''buen modelo''. score de selección de modelo (más parsimonioso).', 'Valor bajo → cerca del polo ''mal modelo''. Opuesto a score de selección de modelo.', '¿más estricto que AIC?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('em_algorithm', 'E-step: Q=E[lnf(Y,Z|θ)]; M-step: θ=argmax Q', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','TRANSFORMAR','ACUMULAR','SELECCIONAR'], 'condiciona por variables latentes, transforma a log, acumula esperanza, selecciona máximo → MLE con datos incompletos', 'algoritmo iterativo para datos con huecos', 'no converge', 'converge rápido', 'algoritmo iterativo para datos con huecos', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''converge rápido''. algoritmo iterativo para datos con huecos.', 'Valor bajo → cerca del polo ''no converge''. Opuesto a algoritmo iterativo para datos con huecos.', '¿MLE con datos incompletos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ar1_formal', 'y_t=c+φy_{t-1}+ε_t', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ACUMULAR'], 'escala pasado por persistencia, acumula con constante+shock → cuánto del ayer queda hoy', 'proceso con memoria', 'estático', 'dinámico', 'proceso con memoria', ARRAY['Los datos son representativos de la población'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso con memoria.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso con memoria.', '¿cuánto del ayer queda hoy?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ma1', 'y_t=μ+ε_t+θε_{t-1}', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ACUMULAR'], 'escala shock anterior, acumula con shock actual → media móvil de sorpresas', 'proceso de memoria corta', 'estático', 'dinámico', 'proceso de memoria corta', ARRAY['Los datos son representativos de la población'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso de memoria corta.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso de memoria corta.', '¿media móvil de sorpresas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('arima', 'φ(L)(1-L)^d y_t=θ(L)ε_t', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','DERIVAR','COMPONER'], 'transforma por operador rezago, diferencia d veces, compone AR×MA → modelo para series con tendencia', 'modelo universal de series temporales', 'bajo', 'alto', 'modelo universal de series temporales', ARRAY['Asume diferenciabilidad — la función es suave','Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. modelo universal de series temporales.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a modelo universal de series temporales.', '¿modelo para series con tendencia?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('funcion_autocorrelacion', 'ρ(k)=γ(k)/γ(0)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR'], 'normaliza covarianza en lag k por varianza → correlación consigo misma en el pasado', 'adjetivo de memoria', 'bajo', 'alto', 'adjetivo de memoria', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de memoria.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de memoria.', '¿correlación consigo misma en el pasado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('adf', 'Δy=α+βy_{t-1}+Σδ_jΔy_{t-j}+ε; H₀:β=0', 'econometria', ARRAY['VERIFICAR'], ARRAY['DERIVAR','ESCALAR','ACUMULAR','COMPARAR'], 'diferencia, escala por nivel rezagado, acumula con rezagos de diferencias, compara β con 0 → ¿hay raíz unitaria?', 'test (¿la serie deambula o es estable?)', 'no significativo', 'significativo', 'test (¿la serie deambula o es estable?)', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test (¿la serie deambula o es estable?).', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test.', '¿¿hay raíz unitaria??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('vecm', 'ΔY=αβ''Y_{t-1}+ΣΓ_jΔY_{t-j}+ε', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPONER','ACUMULAR'], 'compone velocidad×cointegración×nivel, compone dinámica corto plazo, acumula → VAR con corrección de equilibrio', 'sistema con relaciones de largo plazo', 'simple', 'complejo', 'sistema con relaciones de largo plazo', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema con relaciones de largo plazo.', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema con relaciones de largo plazo.', '¿VAR con corrección de equilibrio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cholesky_var', 'ε=Pu donde PP''=Σ', 'econometria', ARRAY['DESCOMPONER'], ARRAY['TRANSFORMAR','COMPONER'], 'transforma covarianza en triangular, compone → identificar shocks estructurales', 'herramienta de identificación', 'no aplica', 'muy útil', 'herramienta de identificación', ARRAY['Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de identificación.', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de identificación.', '¿identificar shocks estructurales?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('arellano_bond', 'Δy=γΔy_{t-1}+β''Δx+Δε; instr: y_{t-2},...', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','CONDICIONAR'], 'diferencia para eliminar efectos fijos, compone con instrumentos internos, condiciona por exogeneidad → panel dinámico', 'estimación de panel con rezago de la dependiente', 'imprecisa', 'precisa', 'estimación de panel con rezago de la dependiente', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación de panel con rezago de la dependiente.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación de panel con rezago de la dependiente.', '¿panel dinámico?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('late_wald', 'LATE=[E(Y|Z=1)-E(Y|Z=0)]/[E(D|Z=1)-E(D|Z=0)]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR','CONDICIONAR','COMPARAR','NORMALIZAR'], 'condiciona por instrumento, compara outcomes, condiciona por tratamiento, compara takeup, normaliza → efecto para los compliers', 'efecto causal local', 'sin efecto', 'efecto causal fuerte', 'efecto causal local', ARRAY['Asume que las condiciones son observables y verificables','La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto causal fuerte''. efecto causal local.', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a efecto causal local.', '¿efecto para los compliers?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ipw', 'τ̂=(1/n)Σ[DY/ê-(1-D)Y/(1-ê)]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','INVERTIR','COMPONER','ACUMULAR','NORMALIZAR'], 'normaliza por propensity, invierte, compone con outcome, acumula, normaliza → efecto ponderando por probabilidad de tratamiento', 'efecto causal por reponderación', 'sin efecto', 'efecto causal fuerte', 'efecto causal por reponderación', ARRAY['Asume invertibilidad — la función tiene inversa','La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto causal fuerte''. efecto causal por reponderación.', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a efecto causal por reponderación.', '¿efecto ponderando por probabilidad de tratamiento?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bunching', 'elasticidad=b/(z*·Δτ/(1-τ))', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','NORMALIZAR'], 'normaliza exceso de masa por cambio marginal → respuesta comportamental a kinks impositivos', 'elasticidad desde aglomeración en umbrales', 'bajo', 'alto', 'elasticidad desde aglomeración en umbrales', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. elasticidad desde aglomeración en umbrales.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a elasticidad desde aglomeración en umbrales.', '¿respuesta comportamental a kinks impositivos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bayes_theorem_formal', 'p(θ|y)∝L(θ)·π(θ)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','NORMALIZAR'], 'compone verosimilitud×prior, normaliza → creencia actualizada', 'herramienta de aprendizaje (cómo cambias de opinión con datos)', 'no aplica', 'muy útil', 'herramienta de aprendizaje (cómo cambias de opinió', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de aprendizaje (cómo cambias de opinión con datos).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de aprendizaje.', '¿creencia actualizada?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('posterior_conjugada', 'θ|y~N(μ_n,τ_n²) con μ_n=(τ₀⁻²μ₀+nσ⁻²ȳ)/(τ₀⁻²+nσ⁻²)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['INVERTIR','COMPONER','ACUMULAR','NORMALIZAR'], 'invierte precisiones, compone con medias, acumula, normaliza → media ponderada de prior y datos', 'actualización bayesiana cerrada', 'bajo', 'alto', 'actualización bayesiana cerrada', ARRAY['Asume invertibilidad — la función tiene inversa','La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. actualización bayesiana cerrada.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a actualización bayesiana cerrada.', '¿media ponderada de prior y datos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('metropolis_hastings', 'α=min{1, p(θ*)q(θ|θ*)/[p(θ)q(θ*|θ)]}', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','NORMALIZAR','COMPARAR','ACOTAR'], 'compone posterior×propuesta, normaliza, compara ratio, acota por 1 → simular distribución posterior por cadena de Markov', 'algoritmo de simulación (explorar lo desconocido)', 'no converge', 'converge rápido', 'algoritmo de simulación (explorar lo desconocido)', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: poner límites", "operacion": "max(0,x) o clamp", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''converge rápido''. algoritmo de simulación (explorar lo desconocido).', 'Valor bajo → cerca del polo ''no converge''. Opuesto a algoritmo de simulación.', '¿simular distribución posterior por cadena de Markov?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('gibbs', 'θ_j~p(θ_j|θ_{-j},y)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','TRANSFORMAR'], 'condiciona cada parámetro por todos los demás, transforma → MCMC por muestreo condicional', 'algoritmo (descomponer lo complejo en partes simples)', 'no converge', 'converge rápido', 'algoritmo (descomponer lo complejo en partes simpl', ARRAY['Asume que las condiciones son observables y verificables','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''converge rápido''. algoritmo (descomponer lo complejo en partes simples).', 'Valor bajo → cerca del polo ''no converge''. Opuesto a algoritmo.', '¿MCMC por muestreo condicional?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('factor_bayes', 'BF=p(y|M₁)/p(y|M₂)=∫L₁π₁dθ/∫L₂π₂dθ', 'econometria', ARRAY['COMPARAR'], ARRAY['COMPONER','INTEGRAR','COMPONER','INTEGRAR','NORMALIZAR'], 'compone verosimilitud×prior, integra sobre θ para cada modelo, normaliza → evidencia relativa entre modelos', 'comparación de modelos (cuál explica mejor)', 'bajo', 'alto', 'comparación de modelos (cuál explica mejor)', ARRAY['Asume integrabilidad — la función está bien definida','La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. comparación de modelos (cuál explica mejor).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a comparación de modelos.', '¿evidencia relativa entre modelos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bma', 'E[Δ|y]=Σ P(M_k|y)·E[Δ|y,M_k]', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','ACUMULAR'], 'condiciona predicción por modelo, compone con probabilidad posterior del modelo, acumula → predicción promediando sobre incertidumbre de modelo', 'predicción robusta (no apuestes por un solo modelo)', 'bajo', 'alto', 'predicción robusta (no apuestes por un solo modelo', ARRAY['Asume que las condiciones son observables y verificables','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. predicción robusta (no apuestes por un solo modelo).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a predicción robusta.', '¿predicción promediando sobre incertidumbre de modelo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kernel_density', 'f̂(x)=(1/nh)ΣK((x-x_i)/h)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR','TRANSFORMAR','ACUMULAR','NORMALIZAR'], 'compara con cada dato, normaliza por ancho de banda, transforma por kernel, acumula, normaliza → densidad sin asumir forma', 'estimación no paramétrica de forma', 'imprecisa', 'precisa', 'estimación no paramétrica de forma', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación no paramétrica de forma.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación no paramétrica de forma.', '¿densidad sin asumir forma?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('nadaraya_watson', 'm̂(x)=ΣK_h(x-x_i)y_i/ΣK_h(x-x_i)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','COMPONER','ACUMULAR','NORMALIZAR'], 'compara con vecinos, transforma por kernel, compone con outcome, acumula, normaliza → regresión sin asumir linealidad', 'regresión no paramétrica', 'bajo', 'alto', 'regresión no paramétrica', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. regresión no paramétrica.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a regresión no paramétrica.', '¿regresión sin asumir linealidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('teorema_maximo_berge', 'V(θ) continua, x*(θ) uhc', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','SELECCIONAR'], 'condiciona por continuidad del problema, selecciona → la función valor es continua y la solución se comporta bien', 'garantía de regularidad', 'no cumple', 'garantizado', 'garantía de regularidad', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía de regularidad.', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía de regularidad.', '¿la función valor es continua y la solución se comporta bien?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('separacion_hiperplanos', '∃p,c: p·a≥c≥p·b ∀a∈A,b∈B', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR'], 'compone precio×asignación, compara → puedes separar lo eficiente de lo ineficiente con un precio', 'herramienta (base del segundo teorema del bienestar)', 'no aplica', 'muy útil', 'herramienta (base del segundo teorema del bienesta', ARRAY['La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (base del segundo teorema del bienestar).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿puedes separar lo eficiente de lo ineficiente con un precio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('weierstrass', 'f continua en K compacto → alcanza max y min', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','SELECCIONAR'], 'condiciona por continuidad+compacidad, selecciona → el óptimo existe', 'garantía de existencia de solución', 'no cumple', 'garantizado', 'garantía de existencia de solución', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía de existencia de solución.', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía de existencia de solución.', '¿el óptimo existe?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('taylor_multivariante', 'f(x+h)≈f(x)+∇f''h+½h''Hh', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','DERIVAR','DERIVAR','COMPONER','ESCALAR','ACUMULAR'], 'deriva gradiente, compone con dirección, deriva hessiana, compone cuadrático, escala ½, acumula → aproximación local de cualquier función', 'herramienta de aproximación universal', 'no aplica', 'muy útil', 'herramienta de aproximación universal', ARRAY['Asume diferenciabilidad — la función es suave','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de aproximación universal.', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de aproximación universal.', '¿aproximación local de cualquier función?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('diferenciacion_implicita', 'dy/dx=-F_x/F_y', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR','TRANSFORMAR'], 'deriva por x, deriva por y, normaliza, invierte signo → pendiente sin despejar', 'herramienta (derivar sin resolver)', 'no aplica', 'muy útil', 'herramienta (derivar sin resolver)', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (derivar sin resolver).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿pendiente sin despejar?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('jacobiano', 'J=[∂f_i/∂x_j]', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR'], 'deriva cada componente por cada variable → transformación local del espacio', 'matriz de cambio de coordenadas', 'bajo', 'alto', 'matriz de cambio de coordenadas', ARRAY['Asume diferenciabilidad — la función es suave','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. matriz de cambio de coordenadas.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a matriz de cambio de coordenadas.', '¿transformación local del espacio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('edo_lineal', 'ẏ+a(t)y=b(t)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','ESCALAR','ACUMULAR','INTEGRAR'], 'deriva, escala por coeficiente, acumula con forcing, integra para resolver → dinámica lineal', 'proceso lineal con solución cerrada', 'estático', 'dinámico', 'proceso lineal con solución cerrada', ARRAY['Asume diferenciabilidad — la función es suave','Asume integrabilidad — la función está bien definida','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso lineal con solución cerrada.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso lineal con solución cerrada.', '¿dinámica lineal?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('sistema_edo_lineal', 'ẋ=Ax → x(t)=e^(At)x₀', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','TRANSFORMAR'], 'compone estado×matriz, transforma por exponencial matricial → dinámica multivariante', 'sistema dinámico con solución en eigenvalores', 'simple', 'complejo', 'sistema dinámico con solución en eigenvalores', ARRAY['Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. sistema dinámico con solución en eigenvalores.', 'Valor bajo → cerca del polo ''simple''. Opuesto a sistema dinámico con solución en eigenvalores.', '¿dinámica multivariante?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('diagrama_fases', 'ẋ=f(x,y), ẏ=g(x,y); clasificar por eigenvalores', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','TRANSFORMAR','COMPARAR'], 'deriva por cada variable, transforma jacobiano, compara eigenvalores → tipo de equilibrio (nodo, silla, espiral)', 'clasificación de estabilidad', 'bajo', 'alto', 'clasificación de estabilidad', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. clasificación de estabilidad.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a clasificación de estabilidad.', '¿tipo de equilibrio (nodo, silla, espiral)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ecuacion_diferencias', 'x_{t+1}=Ax_t+b → x_t=A^t·x₀+(I-A)⁻¹(I-A^t)b', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','TRANSFORMAR','INVERTIR','ACUMULAR'], 'compone estado×matriz, transforma por potencia t, invierte para estado estacionario, acumula → evolución discreta', 'proceso iterativo con convergencia', 'estático', 'dinámico', 'proceso iterativo con convergencia', ARRAY['Asume invertibilidad — la función tiene inversa','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso iterativo con convergencia.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso iterativo con convergencia.', '¿evolución discreta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ito_formal', 'dX=μdt+σdW', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['ESCALAR','ACUMULAR','COMPONER'], 'escala drift, acumula con difusión, compone → dinámica estocástica fundamental', 'proceso base de toda finanza', 'estático', 'dinámico', 'proceso base de toda finanza', ARRAY['Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''dinámico''. proceso base de toda finanza.', 'Valor bajo → cerca del polo ''estático''. Opuesto a proceso base de toda finanza.', '¿dinámica estocástica fundamental?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('fokker_planck', '∂p/∂t=-∂(μp)/∂x+½∂²(σ²p)/∂x²', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','DERIVAR','DERIVAR','COMPONER','ESCALAR','COMPARAR'], 'deriva densidad por drift, deriva 2x por difusión, compone, escala, compara → cómo evoluciona la distribución de probabilidad', 'evolución de la incertidumbre', 'bajo', 'alto', 'evolución de la incertidumbre', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. evolución de la incertidumbre.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a evolución de la incertidumbre.', '¿cómo evoluciona la distribución de probabilidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('formas_cuadraticas', 'q(x)=x''Ax; def+ si eigenvalores>0', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','TRANSFORMAR'], 'compone vector×matriz×vector, transforma a escalar → signo determina convexidad', 'test de convexidad/concavidad', 'no significativo', 'significativo', 'test de convexidad/concavidad', ARRAY['Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de convexidad/concavidad.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de convexidad/concavidad.', '¿signo determina convexidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('matrices_estocasticas', 'P≥0, Σ_j P_ij=1; π=πP', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR','COMPONER','SELECCIONAR'], 'normaliza filas a suma 1, compone distribución×transición, selecciona punto fijo → distribución de largo plazo', 'estado estacionario de cadena de Markov', 'bajo', 'alto', 'estado estacionario de cadena de Markov', ARRAY['Asume que el óptimo existe y es alcanzable','La normalización asume que el denominador es significativo','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. estado estacionario de cadena de Markov.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a estado estacionario de cadena de Markov.', '¿distribución de largo plazo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('proyeccion_ortogonal', 'P_X=X(X''X)⁻¹X''', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','COMPONER'], 'compone X×inversaX''X×X'' → proyecta al espacio columna (OLS = P_X·y)', 'herramienta (la base algebraica de toda regresión)', 'no aplica', 'muy útil', 'herramienta (la base algebraica de toda regresión)', ARRAY['Asume invertibilidad — la función tiene inversa','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (la base algebraica de toda regresión).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿proyecta al espacio columna (OLS = P_X·y)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('convergencia_dominada', 'f_n→f a.e., |f_n|≤g, ∫g<∞ → ∫f_n→∫f', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR','INTEGRAR'], 'compara límite, condiciona por dominación, integra → puedes intercambiar límite e integral', 'garantía técnica (pasar al límite bajo la integral)', 'no cumple', 'garantizado', 'garantía técnica (pasar al límite bajo la integral', ARRAY['Asume que las condiciones son observables y verificables','Asume integrabilidad — la función está bien definida','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía técnica (pasar al límite bajo la integral).', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía técnica.', '¿puedes intercambiar límite e integral?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('integral_lebesgue', '∫fdμ=sup{∫sdμ: s simple, s≤f}', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','INTEGRAR','SELECCIONAR'], 'compara con funciones simples, integra cada una, selecciona supremo → integral generalizada', 'herramienta (integrar cosas que Riemann no puede)', 'no aplica', 'muy útil', 'herramienta (integrar cosas que Riemann no puede)', ARRAY['Asume que el óptimo existe y es alcanzable','Asume integrabilidad — la función está bien definida','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (integrar cosas que Riemann no puede).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿integral generalizada?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('esperanza_condicional_formal', 'E[X|G]: única G-medible con ∫_A E[X|G]dP=∫_A XdP', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','INTEGRAR','COMPARAR'], 'condiciona por información parcial, integra, compara → mejor predicción dada información limitada', 'herramienta (predicción óptima con información parcial)', 'no aplica', 'muy útil', 'herramienta (predicción óptima con información par', ARRAY['Asume que las condiciones son observables y verificables','Asume integrabilidad — la función está bien definida','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (predicción óptima con información parcial).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿mejor predicción dada información limitada?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('representacion_martingala', 'M_t=M_0+∫₀ᵗφ_sdW_s', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['INTEGRAR','ACUMULAR'], 'integra proceso contra browniano, acumula → toda martingala browniana es integral estocástica', 'representación (la estructura de la aleatoriedad justa)', 'bajo', 'alto', 'representación (la estructura de la aleatoriedad j', ARRAY['Asume integrabilidad — la función está bien definida','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Acumular continuamente", "operacion": "suma infinitesimal", "produce": "ÁREA/ACUMULADO CONTINUO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. representación (la estructura de la aleatoriedad justa).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a representación.', '¿toda martingala browniana es integral estocástica?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('level_k', 'L0=uniforme; Lk=BR(L_{k-1})', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','SELECCIONAR'], 'condiciona por nivel de razonamiento inferior, selecciona mejor respuesta → profundidad limitada de pensamiento', 'modelo de racionalidad acotada', 'cota laxa', 'cota ajustada', 'modelo de racionalidad acotada', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''cota ajustada''. modelo de racionalidad acotada.', 'Valor bajo → cerca del polo ''cota laxa''. Opuesto a modelo de racionalidad acotada.', '¿profundidad limitada de pensamiento?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cognitive_hierarchy', 'τ_k=e^(-τ)τ^k/k!; BR contra Poisson truncada', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','NORMALIZAR','CONDICIONAR','SELECCIONAR'], 'transforma por Poisson, normaliza, condiciona por mezcla de niveles, selecciona → distribución de sofisticación en población', 'modelo poblacional de razonamiento', 'bajo', 'alto', 'modelo poblacional de razonamiento', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','La normalización asume que el denominador es significativo','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. modelo poblacional de razonamiento.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a modelo poblacional de razonamiento.', '¿distribución de sofisticación en población?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('choquet_eu', 'V(f)=∫u(f)dν con ν no aditiva', 'conductual', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','INTEGRAR'], 'transforma por utilidad, integra con capacidad no aditiva → utilidad esperada con probabilidades ambiguas', 'decisión bajo ambigüedad profunda', 'bajo', 'alto', 'decisión bajo ambigüedad profunda', ARRAY['Asume integrabilidad — la función está bien definida','Agentes con racionalidad limitada o sesgos'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. decisión bajo ambigüedad profunda.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a decisión bajo ambigüedad profunda.', '¿utilidad esperada con probabilidades ambiguas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('euler_consumidor', 'u''(c_t)=β(1+r)u''(c_{t+1})', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','ESCALAR','DERIVAR','COMPARAR'], 'compara utilidad marginal hoy vs mañana descontada → cuánto consumir hoy vs ahorrar', 'condición de optimalidad temporal', 'no se cumple', 'se cumple', 'condición de optimalidad temporal', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición de optimalidad temporal.', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición de optimalidad temporal.', '¿cuánto consumir hoy vs ahorrar?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('seguro_justo', 'Prima=E[pérdida]; cobertura total si actuarialmente justo', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','ACUMULAR'], 'condiciona por distribución de pérdida, acumula esperanza → precio del riesgo puro', 'sujeto (precio justo del miedo)', 'bajo valor', 'alto valor', 'sujeto (precio justo del miedo)', ARRAY['Asume que las condiciones son observables y verificables','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (precio justo del miedo).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿precio del riesgo puro?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('coaseguros_optimo', 'u''(W-x+I(x))·(1-d''(x))=λ para todo x', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','COMPARAR'], 'deriva utilidad por cobertura, compone con coste, compara con multiplicador → reparto óptimo del riesgo', 'prescripción de cobertura', 'no intervenir', 'intervenir fuerte', 'prescripción de cobertura', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción de cobertura.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción de cobertura.', '¿reparto óptimo del riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('funcion_ingreso', 'R(p)=max p·y s.a. y∈Y', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','CONDICIONAR','SELECCIONAR'], 'compone precio×output, condiciona por tecnología, selecciona máximo → cuánto puedes ganar como máximo', 'sujeto (techo de ingresos)', 'bajo valor', 'alto valor', 'sujeto (techo de ingresos)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto valor''. sujeto (techo de ingresos).', 'Valor bajo → cerca del polo ''bajo valor''. Opuesto a sujeto.', '¿cuánto puedes ganar como máximo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('eficiencia_x', 'Productividad real / Productividad frontera', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['NORMALIZAR'], 'normaliza por la frontera de posibilidades → cuánto desperdicias', 'adjetivo de ineficiencia interna', 'bajo', 'alto', 'adjetivo de ineficiencia interna', ARRAY['La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de ineficiencia interna.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de ineficiencia interna.', '¿cuánto desperdicias?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('segundo_teorema_bienestar', 'Toda asignación PE es equilibrio walrasiano con transferencias', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona por transferencias adecuadas, compara con equilibrio → cualquier eficiencia se alcanza redistribuyendo', 'garantía (la redistribución puede ser eficiente)', 'no cumple', 'garantizado', 'garantía (la redistribución puede ser eficiente)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía (la redistribución puede ser eficiente).', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía.', '¿cualquier eficiencia se alcanza redistribuyendo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('pigouviana', 't*=CMgSocial-CMgPrivado', 'micro', ARRAY['PRESCRIBIR'], ARRAY['COMPARAR'], 'compara coste social con privado → impuesto que internaliza la externalidad', 'prescripción fiscal (precio de contaminar)', 'no intervenir', 'intervenir fuerte', 'prescripción fiscal (precio de contaminar)', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción fiscal (precio de contaminar).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción fiscal.', '¿impuesto que internaliza la externalidad?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('coase', 'Si costes transacción=0, asignación eficiente independiente de derechos', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona por costes cero, compara con eficiencia → negociar resuelve externalidades (en teoría)', 'condición (cuándo sobra el gobierno)', 'no se cumple', 'se cumple', 'condición (cuándo sobra el gobierno)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición (cuándo sobra el gobierno).', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición.', '¿negociar resuelve externalidades (en teoría)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('spne', 'σ* es Nash en todo subjuego', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR','SELECCIONAR'], 'condiciona por cada nodo del juego, compara estrategias, selecciona → amenazas creíbles solamente', 'refinamiento (quita promesas vacías)', 'bajo', 'alto', 'refinamiento (quita promesas vacías)', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. refinamiento (quita promesas vacías).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a refinamiento.', '¿amenazas creíbles solamente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equilibrio_correlacionado', 'Σμ(s)[u(s_i,s_{-i})-u(s''_i,s_{-i})]≥0', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR','ACUMULAR','CONDICIONAR'], 'compone distribución×payoff, compara con desviación, acumula, condiciona por señal → obediencia óptima', 'equilibrio con mediador', 'desequilibrio', 'equilibrio', 'equilibrio con mediador', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''equilibrio''. equilibrio con mediador.', 'Valor bajo → cerca del polo ''desequilibrio''. Opuesto a equilibrio con mediador.', '¿obediencia óptima?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('negociacion_nash', 'max (u₁-d₁)(u₂-d₂)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPARAR','COMPONER','SELECCIONAR'], 'compara con punto de amenaza cada jugador, compone excedentes, selecciona máximo → reparto justo del surplus', 'prescripción de reparto', 'no intervenir', 'intervenir fuerte', 'prescripción de reparto', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción de reparto.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción de reparto.', '¿reparto justo del surplus?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('screening_rs', 'Menú (q_L,t_L),(q_H,t_H) separador', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR','SELECCIONAR'], 'compara contratos, condiciona por autosorteo, selecciona menú óptimo → obligar a revelarse por elección', 'mecanismo de separación', 'inactivo', 'activo', 'mecanismo de separación', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''activo''. mecanismo de separación.', 'Valor bajo → cerca del polo ''inactivo''. Opuesto a mecanismo de separación.', '¿obligar a revelarse por elección?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('akerlof_lemons', 'E[v|p]<p → mercado colapsa', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPARAR'], 'condiciona calidad por precio, compara esperanza con coste → solo los peores venden', 'fallo de mercado (selección adversa destruye comercio)', 'no selecciona', 'selecciona claramente', 'fallo de mercado (selección adversa destruye comer', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''selecciona claramente''. fallo de mercado (selección adversa destruye comercio).', 'Valor bajo → cerca del polo ''no selecciona''. Opuesto a fallo de mercado.', '¿solo los peores venden?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('borch_riesgo', 'u''_P/u''_A=λ constante', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','DERIVAR','NORMALIZAR'], 'deriva utilidades marginales de principal y agente, normaliza → reparto óptimo del riesgo', 'condición de eficiencia en seguros', 'no se cumple', 'se cumple', 'condición de eficiencia en seguros', ARRAY['Asume diferenciabilidad — la función es suave','La normalización asume que el denominador es significativo','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición de eficiencia en seguros.', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición de eficiencia en seguros.', '¿reparto óptimo del riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('bergson_samuelson', 'W=Σα_i·u_i^(1-ε)/(1-ε)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR'], 'transforma por aversión ε, escala por pesos, acumula → bienestar con preferencia ética paramétrica', 'función de bienestar generalizada', 'bajo bienestar', 'alto bienestar', 'función de bienestar generalizada', ARRAY['Agentes racionales que maximizan utilidad'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto bienestar''. función de bienestar generalizada.', 'Valor bajo → cerca del polo ''bajo bienestar''. Opuesto a función de bienestar generalizada.', '¿bienestar con preferencia ética paramétrica?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regulacion_precio_tope', 'p≤c+markup permitido', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','COMPARAR'], 'acumula coste+margen, compara con precio → cuánto puede cobrar un monopolio regulado', 'prescripción regulatoria', 'no intervenir', 'intervenir fuerte', 'prescripción regulatoria', ARRAY['La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción regulatoria.', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción regulatoria.', '¿cuánto puede cobrar un monopolio regulado?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cournot_n_empresas', 'q_i*=(a-c)/(n+1)b; P*=a-(n/(n+1))(a-c)', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','NORMALIZAR'], 'compara demanda-coste, normaliza por número de empresas → más competidores = menos precio', 'equilibrio oligopolístico generalizado', 'desequilibrio', 'equilibrio', 'equilibrio oligopolístico generalizado', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''equilibrio''. equilibrio oligopolístico generalizado.', 'Valor bajo → cerca del polo ''desequilibrio''. Opuesto a equilibrio oligopolístico generalizado.', '¿más competidores = menos precio?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('contestable_market', 'P=CMg incluso con monopolio si entrada libre', 'micro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara precio con coste, condiciona por libertad de entrada → la amenaza de competencia disciplina', 'condición (cuándo el monopolio se comporta bien)', 'no se cumple', 'se cumple', 'condición (cuándo el monopolio se comporta bien)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Agentes racionales que maximizan utilidad'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición (cuándo el monopolio se comporta bien).', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición.', '¿la amenaza de competencia disciplina?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('modelo_ak', 'Y=AK; g=sA-n-δ', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR'], 'compone productividad×capital, compara ahorro con depreciación → crecimiento perpetuo sin rendimientos decrecientes', 'crecimiento endógeno simple', 'contracción', 'expansión', 'crecimiento endógeno simple', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''expansión''. crecimiento endógeno simple.', 'Valor bajo → cerca del polo ''contracción''. Opuesto a crecimiento endógeno simple.', '¿crecimiento perpetuo sin rendimientos decrecientes?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('equivalencia_ricardiana', 'dB=dT_futuro en VP → consumo invariante', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara deuda con impuestos futuros, condiciona por racionalidad → la deuda es impuestos diferidos', 'neutralidad (cómo pagues no importa si eres racional)', 'importa', 'irrelevante', 'neutralidad (cómo pagues no importa si eres racion', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''irrelevante''. neutralidad (cómo pagues no importa si eres racional).', 'Valor bajo → cerca del polo ''importa''. Opuesto a neutralidad.', '¿la deuda es impuestos diferidos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('balassa_samuelson', 'Países productivos tienen precios altos en no-transables', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara productividad entre sectores, condiciona por movilidad laboral → por qué los países ricos son caros', 'explicación de nivel de precios', 'no explica', 'explica completamente', 'explicación de nivel de precios', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''explica completamente''. explicación de nivel de precios.', 'Valor bajo → cerca del polo ''no explica''. Opuesto a explicación de nivel de precios.', '¿por qué los países ricos son caros?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('stolper_samuelson', 'Subida precio bien → sube retorno factor intensivo', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','DERIVAR'], 'compone precio×intensidad factorial, deriva → el comercio beneficia al factor abundante y perjudica al escaso', 'redistribución por comercio', 'bajo', 'alto', 'redistribución por comercio', ARRAY['Asume diferenciabilidad — la función es suave','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. redistribución por comercio.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a redistribución por comercio.', '¿el comercio beneficia al factor abundante y perjudica al escaso?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('rybczynski', 'Más dotación de factor → más producción del bien intensivo en ese factor', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','DERIVAR'], 'compone dotación×intensidad, deriva → efecto de la inmigración/acumulación en la producción', 'efecto de dotación sobre producción', 'bajo', 'alto', 'efecto de dotación sobre producción', ARRAY['Asume diferenciabilidad — la función es suave','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. efecto de dotación sobre producción.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a efecto de dotación sobre producción.', '¿efecto de la inmigración/acumulación en la producción?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('curva_j', 'Balanza empeora antes de mejorar tras devaluación', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPARAR'], 'deriva balanza comercial tras shock de tipo de cambio, compara corto vs largo plazo → paciencia necesaria', 'dinámica de ajuste (lo peor viene primero)', 'estable', 'inestable', 'dinámica de ajuste (lo peor viene primero)', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''inestable''. dinámica de ajuste (lo peor viene primero).', 'Valor bajo → cerca del polo ''estable''. Opuesto a dinámica de ajuste.', '¿paciencia necesaria?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('trinomio_imposible_mundell', 'No ∃ tipo fijo + libre movimiento capital + política monetaria independiente', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'imposibilidad — elige 2 de 3', 'restricción (la trinidad imposible de la macroeconomía abierta)', 'no limita', 'limita severamente', 'restricción (la trinidad imposible de la macroecon', ARRAY['Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Esta fórmula es un resultado teórico/imposibilidad", "operacion": "No requiere cálculo", "produce": "PROPIEDAD del sistema"}]'::jsonb, 'Valor alto → cerca del polo ''limita severamente''. restricción (la trinidad imposible de la macroeconomía abierta).', 'Valor bajo → cerca del polo ''no limita''. Opuesto a restricción.', '¿restricción (la trinidad imposible de la macroeconomía abierta)?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regla_oro_fiscal', 'Déficit ≤ inversión pública neta', 'macro', ARRAY['PRESCRIBIR'], ARRAY['COMPARAR'], 'compara déficit con inversión → solo endeudarse para invertir, no para gastar', 'prescripción fiscal (deuda solo si crea activos)', 'no intervenir', 'intervenir fuerte', 'prescripción fiscal (deuda solo si crea activos)', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''intervenir fuerte''. prescripción fiscal (deuda solo si crea activos).', 'Valor bajo → cerca del polo ''no intervenir''. Opuesto a prescripción fiscal.', '¿solo endeudarse para invertir, no para gastar?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('q_tobin', 'q=Valor mercado capital/Coste reposición; invertir si q>1', 'macro', ARRAY['VALORAR'], ARRAY['NORMALIZAR','COMPARAR'], 'normaliza valor por coste, compara con 1 → ¿vale más crear capital nuevo?', 'señal de inversión', 'sin señal', 'señal fuerte', 'señal de inversión', ARRAY['La normalización asume que el denominador es significativo','La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Dividir por referencia", "operacion": "proyecta por unidad", "produce": "PROPORCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''señal fuerte''. señal de inversión.', 'Valor bajo → cerca del polo ''sin señal''. Opuesto a señal de inversión.', '¿¿vale más crear capital nuevo??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('prima_riesgo_soberano', 'spread=i_país-i_libre_riesgo', 'macro', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR'], 'compara tipo del país con el libre de riesgo → cuánto extra paga un país por su riesgo', 'adjetivo de confianza del mercado', 'bajo', 'alto', 'adjetivo de confianza del mercado', ARRAY['La comparación asume que las escalas son compatibles','Variables agregadas — ignora heterogeneidad individual'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. adjetivo de confianza del mercado.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a adjetivo de confianza del mercado.', '¿cuánto extra paga un país por su riesgo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('varianza_gls', 'Var(β̂_GLS)=(X''Ω⁻¹X)⁻¹', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','INVERTIR','INVERTIR'], 'compone X ponderado, invierte estructura errores, invierte → incertidumbre eficiente', 'varianza mínima bajo heteroscedasticidad', 'bajo', 'alto', 'varianza mínima bajo heteroscedasticidad', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: reciprocar/voltear", "operacion": "1/x", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. varianza mínima bajo heteroscedasticidad.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a varianza mínima bajo heteroscedasticidad.', '¿incertidumbre eficiente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('random_effects', 'y=Xβ+μ_i+ε; GLS con Ω=σ²εI+σ²μ(ιι'')', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR','INVERTIR','COMPONER'], 'compone efectos fijos+aleatorios, acumula varianzas, invierte estructura, compone → panel eficiente si μ exógeno', 'estimación panel con heterogeneidad aleatoria', 'imprecisa', 'precisa', 'estimación panel con heterogeneidad aleatoria', ARRAY['Asume invertibilidad — la función tiene inversa','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Reciprocar/voltear", "operacion": "1/x", "produce": "EJE INVERTIDO"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación panel con heterogeneidad aleatoria.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación panel con heterogeneidad aleatoria.', '¿panel eficiente si μ exógeno?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('arellano_bond_test', 'H₀: no AR(2) en Δε', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPARAR'], 'diferencia errores, compara autocorrelación de orden 2 → ¿instrumentos válidos?', 'test de validez de instrumentos dinámicos', 'no significativo', 'significativo', 'test de validez de instrumentos dinámicos', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de validez de instrumentos dinámicos.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de validez de instrumentos dinámicos.', '¿¿instrumentos válidos??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('johansen_formal', 'LR_trace=-TΣln(1-λ̂_i)', 'econometria', ARRAY['VERIFICAR'], ARRAY['TRANSFORMAR','ACUMULAR','ESCALAR'], 'transforma eigenvalores a log, acumula, escala por T → cuántas relaciones de largo plazo existen', 'test de cointegración multivariante', 'no significativo', 'significativo', 'test de cointegración multivariante', ARRAY['Los datos son representativos de la población'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de cointegración multivariante.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de cointegración multivariante.', '¿cuántas relaciones de largo plazo existen?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('descomposicion_espectral_ts', 'f(ω)=(1/2π)Σγ(k)e^(-ikω)', 'econometria', ARRAY['DESCOMPONER'], ARRAY['COMPONER','TRANSFORMAR','ACUMULAR','NORMALIZAR'], 'compone autocovarianza×exponencial compleja, transforma Fourier, acumula, normaliza → qué frecuencias dominan', 'descomposición frecuencial', 'un solo factor', 'múltiples factores', 'descomposición frecuencial', ARRAY['La normalización asume que el denominador es significativo','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición frecuencial.', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición frecuencial.', '¿qué frecuencias dominan?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('granger_formal', 'H₀: coefs y₂ rezagados = 0 en ecuación y₁', 'econometria', ARRAY['VERIFICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara modelo con y sin rezagos de la otra variable, condiciona → ¿el pasado de Y₂ ayuda a predecir Y₁?', 'test de causalidad temporal', 'no significativo', 'significativo', 'test de causalidad temporal', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''significativo''. test de causalidad temporal.', 'Valor bajo → cerca del polo ''no significativo''. Opuesto a test de causalidad temporal.', '¿¿el pasado de Y₂ ayuda a predecir Y₁??')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hodrick_prescott_formal', 'min Σ(y-τ)²+λΣ[(τ_{t+1}-τ_t)-(τ_t-τ_{t-1})]²', 'econometria', ARRAY['DESCOMPONER'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','COMPARAR','COMPARAR','TRANSFORMAR','ACUMULAR','ESCALAR','ACUMULAR','SELECCIONAR'], 'balancea ajuste a datos vs suavidad de tendencia → separa ciclo de tendencia', 'descomposición trend+cycle', 'un solo factor', 'múltiples factores', 'descomposición trend+cycle', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición trend+cycle.', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición trend+cycle.', '¿separa ciclo de tendencia?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('tobit_formal', 'y*=x''β+ε; y=max(0,y*); MLE con censura', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACOTAR','CONDICIONAR','SELECCIONAR'], 'compone modelo latente, acota por cero, condiciona por censura, selecciona MLE → estimar lo que está detrás del cero', 'estimación con datos censurados', 'imprecisa', 'precisa', 'estimación con datos censurados', ARRAY['Asume que las condiciones son observables y verificables','Asume que el óptimo existe y es alcanzable','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Poner límites", "operacion": "max(0,x) o clamp", "produce": "ACOTADO"}, {"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación con datos censurados.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación con datos censurados.', '¿estimar lo que está detrás del cero?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('heckman_seleccion', 'E[y|seleccionado]=x''β+ρσ·λ(z''γ)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','COMPONER','ACUMULAR'], 'condiciona por selección (quién observamos), compone corrección lambda, acumula → corregir por quién elige participar', 'corrección de sesgo de selección', 'no selecciona', 'selecciona claramente', 'corrección de sesgo de selección', ARRAY['Asume que las condiciones son observables y verificables','Los datos son representativos de la población'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''selecciona claramente''. corrección de sesgo de selección.', 'Valor bajo → cerca del polo ''no selecciona''. Opuesto a corrección de sesgo de selección.', '¿corregir por quién elige participar?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('quantile_regression', 'min Σ ρ_τ(y_i-x''_iβ) donde ρ_τ(u)=u(τ-I(u<0))', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','SELECCIONAR'], 'compara residuo asimétrico, transforma por cuantil τ, acumula, selecciona mínimo → efecto en cada punto de la distribución', 'efecto heterogéneo (no solo la media)', 'bajo', 'alto', 'efecto heterogéneo (no solo la media)', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. efecto heterogéneo (no solo la media).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a efecto heterogéneo.', '¿efecto en cada punto de la distribución?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('panel_feis', 'Within + first-differencing + instrumentos', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','CONDICIONAR'], 'diferencia para eliminar fijos, compone con instrumentos, condiciona → panel con tendencias individuales', 'estimación panel con pendientes individuales', 'imprecisa', 'precisa', 'estimación panel con pendientes individuales', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''precisa''. estimación panel con pendientes individuales.', 'Valor bajo → cerca del polo ''imprecisa''. Opuesto a estimación panel con pendientes individuales.', '¿panel con tendencias individuales?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('synthetic_did', 'SDiD = DiD + pesos de control sintético', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','COMPARAR','COMPARAR','ESCALAR'], 'combina DiD con control sintético → causalidad con controles óptimos', 'efecto causal robusto', 'sin efecto', 'efecto causal fuerte', 'efecto causal robusto', ARRAY['La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: ponderar/amplificar", "operacion": "multiplica por factor", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto causal fuerte''. efecto causal robusto.', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a efecto causal robusto.', '¿causalidad con controles óptimos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('event_study', 'y=Σ β_k·D_{t=k}+controles', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR','COMPARAR'], 'compone dummies×coeficientes por periodo, acumula, compara con pre-tratamiento → efecto dinámico del evento', 'narrativa causal temporal', 'sin efecto', 'efecto grande y dinámico', 'narrativa causal temporal', ARRAY['La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto grande y dinámico''. narrativa causal temporal.', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a narrativa causal temporal.', '¿efecto dinámico del evento?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regression_kink', 'τ̂=cambio pendiente en el kink', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPARAR'], 'deriva relación a ambos lados del kink, compara pendientes → efecto causal en discontinuidades de pendiente', 'efecto causal en kink', 'sin efecto', 'efecto causal fuerte', 'efecto causal en kink', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Los datos son representativos de la población'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''efecto causal fuerte''. efecto causal en kink.', 'Valor bajo → cerca del polo ''sin efecto''. Opuesto a efecto causal en kink.', '¿efecto causal en discontinuidades de pendiente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('shift_share_bartik', 'Z_i=Σ_k s_{ik}·g_k (shares×crecimiento nacional)', 'econometria', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','ACUMULAR'], 'compone estructura industrial local × crecimiento nacional por sector, acumula → instrumento de exposición diferencial', 'instrumento para shocks de demanda local', 'bajo', 'alto', 'instrumento para shocks de demanda local', ARRAY['Los datos son representativos de la población'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. instrumento para shocks de demanda local.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a instrumento para shocks de demanda local.', '¿instrumento de exposición diferencial?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('regla_cadena_multi', 'df/dt=Σ(∂f/∂x_i)·(dx_i/dt)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','ACUMULAR'], 'deriva por cada variable, compone con velocidad de cada variable, acumula → cambio total de una función compuesta', 'herramienta de propagación', 'no aplica', 'muy útil', 'herramienta de propagación', ARRAY['Asume diferenciabilidad — la función es suave','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: agregar/sumar", "operacion": "acumula en un eje", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de propagación.', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de propagación.', '¿cambio total de una función compuesta?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('teorema_envolvente_formal', 'dV*/dα=∂L/∂α|_{x=x*}', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','CONDICIONAR'], 'deriva valor óptimo respecto a parámetro, condicionado al óptimo → cómo cambia el máximo cuando cambias las reglas', 'sensibilidad del óptimo (el precio sombra)', 'insensible', 'hipersensible', 'sensibilidad del óptimo (el precio sombra)', ARRAY['Asume que las condiciones son observables y verificables','Asume diferenciabilidad — la función es suave','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''hipersensible''. sensibilidad del óptimo (el precio sombra).', 'Valor bajo → cerca del polo ''insensible''. Opuesto a sensibilidad del óptimo.', '¿cómo cambia el máximo cuando cambias las reglas?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('svd', 'A=UΣV''', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR'], 'transforma cualquier matriz en rotación×escalado×rotación → factorización fundamental', 'descomposición universal de cualquier transformación lineal', 'un solo factor', 'múltiples factores', 'descomposición universal de cualquier transformaci', ARRAY['Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''múltiples factores''. descomposición universal de cualquier transformación lineal.', 'Valor bajo → cerca del polo ''un solo factor''. Opuesto a descomposición universal de cualquier transformación lineal.', '¿factorización fundamental?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('eigenvalor_ecuacion', 'Av=λv; det(A-λI)=0', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR','SELECCIONAR'], 'compone matriz×vector, compara con escalar×vector, selecciona → direcciones que la transformación solo escala', 'direcciones fundamentales del sistema', 'simple', 'complejo', 'direcciones fundamentales del sistema', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''complejo''. direcciones fundamentales del sistema.', 'Valor bajo → cerca del polo ''simple''. Opuesto a direcciones fundamentales del sistema.', '¿direcciones que la transformación solo escala?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('rango_condicion', 'rank=dim(imagen); κ=λ_max/λ_min', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['TRANSFORMAR','NORMALIZAR'], 'transforma a eigenvalores, normaliza max/min → dimensión efectiva y estabilidad numérica', 'diagnóstico de salud numérica', 'bajo', 'alto', 'diagnóstico de salud numérica', ARRAY['La normalización asume que el denominador es significativo','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Cambiar de eje/escala", "operacion": "transforma representación", "produce": "NUEVA ESCALA"}, {"paso": "Paso final: dividir por referencia", "operacion": "proyecta por unidad", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. diagnóstico de salud numérica.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a diagnóstico de salud numérica.', '¿dimensión efectiva y estabilidad numérica?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('traza_determinante', 'tr(A)=Σλ_i; det(A)=Πλ_i', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','COMPONER'], 'acumula eigenvalores (traza), compone eigenvalores (determinante) → resumen de la transformación', 'estadísticos resumen de una matriz', 'bajo', 'alto', 'estadísticos resumen de una matriz', ARRAY['Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: combinar dos ejes", "operacion": "multiplica variables", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. estadísticos resumen de una matriz.', 'Valor bajo → cerca del polo ''bajo''. Opuesto a estadísticos resumen de una matriz.', '¿resumen de la transformación?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('lema_farkas', '∃x≥0:Ax=b ó ∃y:A''y≥0,b''y<0 (no ambos)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara factibilidad con certificado de infactibilidad → uno u otro, nunca ambos', 'dualidad (la base de toda programación lineal)', 'bajo', 'alto', 'dualidad (la base de toda programación lineal)', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. dualidad (la base de toda programación lineal).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a dualidad.', '¿uno u otro, nunca ambos?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('minimax', 'max_x min_y f(x,y)=min_y max_x f(x,y) bajo convexidad-concavidad', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['SELECCIONAR','SELECCIONAR','COMPARAR'], 'selecciona peor caso para ti, selecciona mejor caso para el rival, compara → en juegos de suma cero, el orden no importa', 'dualidad de juegos (von Neumann)', 'bajo', 'alto', 'dualidad de juegos (von Neumann)', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "PUNTO ÓPTIMO"}, {"paso": "Elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "PUNTO ÓPTIMO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. dualidad de juegos (von Neumann).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a dualidad de juegos.', '¿en juegos de suma cero, el orden no importa?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('ley_iterada_expectativas', 'E[E[X|G]]=E[X]', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','CONDICIONAR'], 'condiciona dos veces → la esperanza de la mejor predicción parcial es la mejor predicción total', 'consistencia de la información (no puedes crear información refinando)', 'bajo', 'alto', 'consistencia de la información (no puedes crear in', ARRAY['Asume que las condiciones son observables y verificables','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. consistencia de la información (no puedes crear información refinando).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a consistencia de la información.', '¿la esperanza de la mejor predicción parcial es la mejor predicción tot?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('convergencia_monotona', '0≤f_n↑f → ∫f_n↑∫f', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','INTEGRAR'], 'compara funciones crecientes, integra → puedes intercambiar límite e integral si todo sube', 'garantía técnica', 'no cumple', 'garantizado', 'garantía técnica', ARRAY['Asume integrabilidad — la función está bien definida','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: acumular continuamente", "operacion": "suma infinitesimal", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía técnica.', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía técnica.', '¿puedes intercambiar límite e integral si todo sube?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('portmanteau', '∀ abierto O: liminf P_n(O)≥P(O); ∀ cerrado C: limsup P_n(C)≤P(C)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','CONDICIONAR'], 'compara probabilidades en abiertos y cerrados, condiciona → convergencia débil de distribuciones', 'definición de convergencia en distribución', 'diverge', 'converge', 'definición de convergencia en distribución', ARRAY['Asume que las condiciones son observables y verificables','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''converge''. definición de convergencia en distribución.', 'Valor bajo → cerca del polo ''diverge''. Opuesto a definición de convergencia en distribución.', '¿convergencia débil de distribuciones?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('kolmogorov', 'sup_x|F_n(x)-F(x)|→0 a.s.', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','SELECCIONAR'], 'compara distribución empírica con teórica, selecciona máxima diferencia → la distribución empírica converge uniformemente', 'garantía (los datos eventualmente muestran la distribución real)', 'no cumple', 'garantizado', 'garantía (los datos eventualmente muestran la dist', ARRAY['Asume que el óptimo existe y es alcanzable','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Paso final: elegir extremo/óptimo", "operacion": "max/min/argmax", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía (los datos eventualmente muestran la distribución real).', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía.', '¿la distribución empírica converge uniformemente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('slutsky_theorem', 'X_n→d X, Y_n→p c → X_n+Y_n→d X+c', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['ACUMULAR','CONDICIONAR'], 'acumula convergencias, condiciona por tipo → las convergencias se combinan limpiamente', 'herramienta (combinar límites en probabilidad)', 'no aplica', 'muy útil', 'herramienta (combinar límites en probabilidad)', ARRAY['Asume que las condiciones son observables y verificables','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Agregar/sumar", "operacion": "acumula en un eje", "produce": "TOTAL acumulado"}, {"paso": "Paso final: restringir universo", "operacion": "dado que/si", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta (combinar límites en probabilidad).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta.', '¿las convergencias se combinan limpiamente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('cramer_wold', 'X_n→d X ⟺ t''X_n→d t''X ∀t', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPONER','COMPARAR'], 'compone con cualquier dirección, compara → convergencia multivariante = convergencia en toda dirección', 'reducción (lo multivariante se reduce a lo univariante)', 'bajo', 'alto', 'reducción (lo multivariante se reduce a lo univari', ARRAY['La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''alto''. reducción (lo multivariante se reduce a lo univariante).', 'Valor bajo → cerca del polo ''bajo''. Opuesto a reducción.', '¿convergencia multivariante = convergencia en toda dirección?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('contraccion_operador_formal', '||Tf-Tg||≤β||f-g|| con β<1 → ∃! punto fijo', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['COMPARAR','ESCALAR','COMPARAR'], 'compara imágenes, escala por contracción β<1, compara → cada iteración se acerca al punto fijo', 'garantía algorítmica (la iteración converge)', 'no cumple', 'garantizado', 'garantía algorítmica (la iteración converge)', ARRAY['La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir distancia", "operacion": "compara dos valores", "produce": "DIFERENCIA/POSICIÓN"}, {"paso": "Ponderar/amplificar", "operacion": "multiplica por factor", "produce": "PONDERADO"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''garantizado''. garantía algorítmica (la iteración converge).', 'Valor bajo → cerca del polo ''no cumple''. Opuesto a garantía algorítmica.', '¿cada iteración se acerca al punto fijo?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('hahn_banach', 'Extensión lineal continua de funcional en subespacio', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['CONDICIONAR','TRANSFORMAR'], 'condiciona por subespacio, transforma extensión → puedes extender cualquier funcional lineal', 'herramienta de dualidad (base de la economía del bienestar)', 'no aplica', 'muy útil', 'herramienta de dualidad (base de la economía del b', ARRAY['Asume que las condiciones son observables y verificables','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Restringir universo", "operacion": "dado que/si", "produce": "CONTEXTO REDUCIDO"}, {"paso": "Paso final: cambiar de eje/escala", "operacion": "transforma representación", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''muy útil''. herramienta de dualidad (base de la economía del bienestar).', 'Valor bajo → cerca del polo ''no aplica''. Opuesto a herramienta de dualidad.', '¿puedes extender cualquier funcional lineal?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, lectura, resultado, polo_bajo, polo_alto, eje, presupuestos, razonamiento, si_alto, si_bajo, pregunta)
VALUES ('separacion_segundo_orden', 'Si f cóncava, f(x)≤f(x*)+∇f(x*)''(x-x*)', 'matematica', ARRAY['DIAGNOSTICAR'], ARRAY['DERIVAR','COMPONER','COMPARAR'], 'deriva en el óptimo, compone con dirección, compara → la función está por debajo de su tangente', 'condición de optimalidad global (no solo local)', 'no se cumple', 'se cumple', 'condición de optimalidad global (no solo local)', ARRAY['Asume diferenciabilidad — la función es suave','La comparación asume que las escalas son compatibles','Condiciones técnicas de regularidad cumplidas'], '[{"paso": "Medir velocidad de cambio", "operacion": "¿cuánto cambia por unidad?", "produce": "VELOCIDAD/SENSIBILIDAD"}, {"paso": "Combinar dos ejes", "operacion": "multiplica variables", "produce": "INTERACCIÓN"}, {"paso": "Paso final: medir distancia", "operacion": "compara dos valores", "produce": "RESULTADO FINAL"}]'::jsonb, 'Valor alto → cerca del polo ''se cumple''. condición de optimalidad global (no solo local).', 'Valor bajo → cerca del polo ''no se cumple''. Opuesto a condición de optimalidad global.', '¿la función está por debajo de su tangente?')
ON CONFLICT (nombre) DO UPDATE SET
  formula=EXCLUDED.formula, rama=EXCLUDED.rama, finalidad=EXCLUDED.finalidad,
  gramatica=EXCLUDED.gramatica, lectura=EXCLUDED.lectura, resultado=EXCLUDED.resultado,
  polo_bajo=EXCLUDED.polo_bajo, polo_alto=EXCLUDED.polo_alto, eje=EXCLUDED.eje,
  presupuestos=EXCLUDED.presupuestos, razonamiento=EXCLUDED.razonamiento,
  si_alto=EXCLUDED.si_alto, si_bajo=EXCLUDED.si_bajo, pregunta=EXCLUDED.pregunta;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, polo_bajo, polo_alto, eje, pregunta)
VALUES ('marco_jaccard', 'J(A,B) = |A∩B| / |A∪B|', 'conjuntos', ARRAY['DIAGNOSTICAR'], ARRAY[]::TEXT[], 'mitades completamente diferentes', 'mitades idénticas', 'similitud entre conjuntos', '¿La primera y segunda mitad del texto usan las mismas funciones?')
ON CONFLICT (nombre) DO NOTHING;
INSERT INTO catalogo_formulas (nombre, formula, rama, finalidad, gramatica, polo_bajo, polo_alto, eje, pregunta)
VALUES ('marco_emergencia', 'Var(Σx_i) / Σ Var(x_i)', 'sistemas', ARRAY['MEDIR_RIESGO'], ARRAY[]::TEXT[], 'no hay emergencia', 'la conclusión es nueva', 'propiedades emergentes', '¿La conclusión emerge como algo nuevo o se deduce de lo anterior?')
ON CONFLICT (nombre) DO NOTHING;



-- Isomorfismos de gramática
DELETE FROM isomorfismos_gramatica;
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','NORMALIZAR','NORMALIZAR'], 'COMPARAR→TRANSFORMAR→ACUMULAR→NORMALIZAR→NORMALIZAR', ARRAY['skewness','kurtosis'], ARRAY['estadistica'], 2, false, 'Estas 2 fórmulas comparten la gramática COMPARAR→TRANSFORMAR→ACUMULAR→NORMALIZAR→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR'], 'DERIVAR', ARRAY['utilidad_marginal','coste_marginal','lema_shephard','hotelling','jacobiano'], ARRAY['micro','matematica'], 5, true, 'Estas 5 fórmulas comparten la gramática DERIVAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','DERIVAR','NORMALIZAR'], 'DERIVAR→DERIVAR→NORMALIZAR', ARRAY['tasa_marginal_sustitucion','borch_riesgo'], ARRAY['micro'], 2, false, 'Estas 2 fórmulas comparten la gramática DERIVAR→DERIVAR→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','NORMALIZAR'], 'COMPARAR→NORMALIZAR', ARRAY['indice_lerner','tasa_crecimiento','output_gap','sharpe','cournot_n_empresas'], ARRAY['macro','finanzas','micro'], 5, true, 'Estas 5 fórmulas comparten la gramática COMPARAR→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, finanzas, micro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','CONDICIONAR','SELECCIONAR'], 'COMPARAR→CONDICIONAR→SELECCIONAR', ARRAY['equilibrio_nash','señalizacion_spence','screening_rs'], ARRAY['micro'], 3, false, 'Estas 3 fórmulas comparten la gramática COMPARAR→CONDICIONAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','COMPONER','COMPARAR','SELECCIONAR'], 'COMPONER→COMPONER→COMPARAR→SELECCIONAR', ARRAY['solow_steady_state','funcion_beneficio'], ARRAY['macro','micro'], 2, true, 'Estas 2 fórmulas comparten la gramática COMPONER→COMPONER→COMPARAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','ESCALAR','ACUMULAR'], 'COMPARAR→ESCALAR→ACUMULAR', ARRAY['curva_phillips','capm'], ARRAY['macro','finanzas'], 2, true, 'Estas 2 fórmulas comparten la gramática COMPARAR→ESCALAR→ACUMULAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, finanzas.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR'], 'COMPARAR', ARRAY['ecuacion_fisher','modigliani_miller','dominancia_estocastica_1','bertrand','pigouviana','regla_oro_fiscal','prima_riesgo_soberano'], ARRAY['macro','micro','finanzas'], 7, true, 'Estas 7 fórmulas comparten la gramática COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro, finanzas.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','NORMALIZAR'], 'COMPONER→NORMALIZAR', ARRAY['velocidad_dinero','bayes_theorem_formal'], ARRAY['macro','econometria'], 2, true, 'Estas 2 fórmulas comparten la gramática COMPONER→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['ESCALAR','COMPARAR'], 'ESCALAR→COMPARAR', ARRAY['var_parametrico','lagrangiano'], ARRAY['optimizacion','finanzas'], 2, true, 'Estas 2 fórmulas comparten la gramática ESCALAR→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: optimizacion, finanzas.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','INVERTIR','COMPONER'], 'COMPONER→INVERTIR→COMPONER', ARRAY['ols','iv_2sls','lm_score_test','proyeccion_ortogonal'], ARRAY['matematica','econometria'], 4, true, 'Estas 4 fórmulas comparten la gramática COMPONER→INVERTIR→COMPONER — hacen la MISMA operación sobre dominios diferentes. Cross-domain: matematica, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['NORMALIZAR'], 'NORMALIZAR', ARRAY['t_statistic','tipo_cambio_ppc_formal','funcion_autocorrelacion','eficiencia_x'], ARRAY['macro','micro','econometria'], 4, true, 'Estas 4 fórmulas comparten la gramática NORMALIZAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','TRANSFORMAR','ACUMULAR','SELECCIONAR'], 'CONDICIONAR→TRANSFORMAR→ACUMULAR→SELECCIONAR', ARRAY['mle','em_algorithm'], ARRAY['econometria'], 2, false, 'Estas 2 fórmulas comparten la gramática CONDICIONAR→TRANSFORMAR→ACUMULAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['ACUMULAR','ACUMULAR','COMPARAR'], 'ACUMULAR→ACUMULAR→COMPARAR', ARRAY['exceso_demanda','vcg'], ARRAY['micro'], 2, false, 'Estas 2 fórmulas comparten la gramática ACUMULAR→ACUMULAR→COMPARAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','ACUMULAR'], 'COMPONER→ACUMULAR', ARRAY['ley_walras','var','impulso_respuesta','agregacion_engel','utilidad_esperada_vnm','shift_share_bartik'], ARRAY['micro','econometria'], 6, true, 'Estas 6 fórmulas comparten la gramática COMPONER→ACUMULAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['SELECCIONAR'], 'SELECCIONAR', ARRAY['bienestar_rawls','regla_friedman'], ARRAY['macro','micro'], 2, true, 'Estas 2 fórmulas comparten la gramática SELECCIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','SELECCIONAR'], 'CONDICIONAR→SELECCIONAR', ARRAY['punto_fijo_brouwer','utilidad_indirecta','teorema_maximo_berge','weierstrass','level_k'], ARRAY['conductual','micro','matematica'], 5, true, 'Estas 5 fórmulas comparten la gramática CONDICIONAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: conductual, micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','CONDICIONAR','SELECCIONAR'], 'COMPONER→CONDICIONAR→SELECCIONAR', ARRAY['frontera_eficiente','stackelberg','frontera_varianza_minima','funcion_ingreso'], ARRAY['micro','finanzas','macro'], 4, true, 'Estas 4 fórmulas comparten la gramática COMPONER→CONDICIONAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, finanzas, macro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['ESCALAR','ACUMULAR'], 'ESCALAR→ACUMULAR', ARRAY['ar1','ar1_formal','ma1'], ARRAY['econometria'], 3, false, 'Estas 3 fórmulas comparten la gramática ESCALAR→ACUMULAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','TRANSFORMAR','ACUMULAR','COMPARAR','COMPARAR','TRANSFORMAR','ACUMULAR','ESCALAR','ACUMULAR','SELECCIONAR'], 'COMPARAR→TRANSFORMAR→ACUMULAR→COMPARAR→COMPARAR→TRANSFORMAR→ACUMULAR→ESCALAR→ACUMULAR→SELECCIONAR', ARRAY['hodrick_prescott','hodrick_prescott_formal'], ARRAY['macro','econometria'], 2, true, 'Estas 2 fórmulas comparten la gramática COMPARAR→TRANSFORMAR→ACUMULAR→COMPARAR→COMPARAR→TRANSFORMAR→ACUMULAR→ESCALAR→ACUMULAR→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY[]::TEXT[], '', ARRAY['vickrey','myerson_satterthwaite','arrow_imposibilidad','gibbard_satterthwaite','trinomio_imposible_mundell'], ARRAY['macro','micro'], 5, true, 'Estas 5 fórmulas comparten la gramática  — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','DERIVAR','NORMALIZAR','TRANSFORMAR'], 'DERIVAR→DERIVAR→NORMALIZAR→TRANSFORMAR', ARRAY['identidad_roy','aversion_riesgo_arrow_pratt','diferenciacion_implicita'], ARRAY['micro','matematica'], 3, true, 'Estas 3 fórmulas comparten la gramática DERIVAR→DERIVAR→NORMALIZAR→TRANSFORMAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','COMPONER','SELECCIONAR'], 'CONDICIONAR→COMPONER→SELECCIONAR', ARRAY['funcion_gasto','funcion_coste','demanda_hicksiana'], ARRAY['micro'], 3, false, 'Estas 3 fórmulas comparten la gramática CONDICIONAR→COMPONER→SELECCIONAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','CONDICIONAR'], 'COMPARAR→CONDICIONAR', ARRAY['pareto_eficiencia','folk_theorem','incentive_compatibility','nucleo_economia','heckscher_ohlin','melitz_exportadores','contestable_market','equivalencia_ricardiana','balassa_samuelson','granger_formal','lema_farkas','portmanteau'], ARRAY['macro','matematica','micro','econometria'], 12, true, 'Estas 12 fórmulas comparten la gramática COMPARAR→CONDICIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, matematica, micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','CONDICIONAR'], 'DERIVAR→CONDICIONAR', ARRAY['envelope_theorem','teorema_envolvente_formal'], ARRAY['micro','matematica'], 2, true, 'Estas 2 fórmulas comparten la gramática DERIVAR→CONDICIONAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['TRANSFORMAR','ESCALAR','ACUMULAR'], 'TRANSFORMAR→ESCALAR→ACUMULAR', ARRAY['mankiw_romer_weil','aic','bergson_samuelson'], ARRAY['macro','micro','econometria'], 3, true, 'Estas 3 fórmulas comparten la gramática TRANSFORMAR→ESCALAR→ACUMULAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','COMPARAR'], 'CONDICIONAR→COMPARAR', ARRAY['gauss_markov','martingala','revenue_equivalence','segundo_teorema_bienestar','coase','akerlof_lemons'], ARRAY['matematica','micro','econometria'], 6, true, 'Estas 6 fórmulas comparten la gramática CONDICIONAR→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: matematica, micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','TRANSFORMAR'], 'COMPONER→TRANSFORMAR', ARRAY['probit','sistema_edo_lineal','formas_cuadraticas'], ARRAY['matematica','econometria'], 3, true, 'Estas 3 fórmulas comparten la gramática COMPONER→TRANSFORMAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: matematica, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','INTEGRAR'], 'COMPARAR→INTEGRAR', ARRAY['dominancia_estocastica_2','convergencia_monotona'], ARRAY['micro','matematica'], 2, true, 'Estas 2 fórmulas comparten la gramática COMPARAR→INTEGRAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['TRANSFORMAR','NORMALIZAR'], 'TRANSFORMAR→NORMALIZAR', ARRAY['utilidad_crra','rango_condicion'], ARRAY['micro','matematica'], 2, true, 'Estas 2 fórmulas comparten la gramática TRANSFORMAR→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['TRANSFORMAR','ESCALAR','COMPONER','ACUMULAR'], 'TRANSFORMAR→ESCALAR→COMPONER→ACUMULAR', ARRAY['translog','bic'], ARRAY['micro','econometria'], 2, true, 'Estas 2 fórmulas comparten la gramática TRANSFORMAR→ESCALAR→COMPONER→ACUMULAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPARAR','COMPONER','NORMALIZAR'], 'COMPARAR→COMPONER→NORMALIZAR', ARRAY['calvo_parametro','ccapm'], ARRAY['macro'], 2, false, 'Estas 2 fórmulas comparten la gramática COMPARAR→COMPONER→NORMALIZAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['ACUMULAR','COMPARAR'], 'ACUMULAR→COMPARAR', ARRAY['condicion_marshall_lerner','regulacion_precio_tope'], ARRAY['macro','micro'], 2, true, 'Estas 2 fórmulas comparten la gramática ACUMULAR→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, micro.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','COMPONER','CONDICIONAR'], 'DERIVAR→COMPONER→CONDICIONAR', ARRAY['arellano_bond','panel_feis'], ARRAY['econometria'], 2, false, 'Estas 2 fórmulas comparten la gramática DERIVAR→COMPONER→CONDICIONAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','TRANSFORMAR'], 'CONDICIONAR→TRANSFORMAR', ARRAY['gibbs','hahn_banach'], ARRAY['matematica','econometria'], 2, true, 'Estas 2 fórmulas comparten la gramática CONDICIONAR→TRANSFORMAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: matematica, econometria.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['CONDICIONAR','COMPONER','ACUMULAR'], 'CONDICIONAR→COMPONER→ACUMULAR', ARRAY['bma','heckman_seleccion'], ARRAY['econometria'], 2, false, 'Estas 2 fórmulas comparten la gramática CONDICIONAR→COMPONER→ACUMULAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','COMPARAR'], 'COMPONER→COMPARAR', ARRAY['separacion_hiperplanos','modelo_ak','cramer_wold'], ARRAY['macro','matematica'], 3, true, 'Estas 3 fórmulas comparten la gramática COMPONER→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','COMPONER','COMPARAR'], 'DERIVAR→COMPONER→COMPARAR', ARRAY['coaseguros_optimo','separacion_segundo_orden'], ARRAY['micro','matematica'], 2, true, 'Estas 2 fórmulas comparten la gramática DERIVAR→COMPONER→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: micro, matematica.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['COMPONER','DERIVAR'], 'COMPONER→DERIVAR', ARRAY['stolper_samuelson','rybczynski'], ARRAY['macro'], 2, false, 'Estas 2 fórmulas comparten la gramática COMPONER→DERIVAR — hacen la MISMA operación sobre dominios diferentes.');
INSERT INTO isomorfismos_gramatica (gramatica, gramatica_texto, formulas, ramas, n_formulas, es_cross_domain, significado)
VALUES (ARRAY['DERIVAR','COMPARAR'], 'DERIVAR→COMPARAR', ARRAY['curva_j','arellano_bond_test','regression_kink'], ARRAY['macro','econometria'], 3, true, 'Estas 3 fórmulas comparten la gramática DERIVAR→COMPARAR — hacen la MISMA operación sobre dominios diferentes. Cross-domain: macro, econometria.');



-- Red de preguntas encadenadas
DELETE FROM red_preguntas;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('varianza', 'alto', 'skewness', 'disperso → ¿hacia dónde se inclina el riesgo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('varianza', 'alto', 'kurtosis', 'disperso → ¿cuán probables son los extremos?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('varianza', 'alto', 'gini', 'disperso → ¿es desigualdad o heterogeneidad?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('varianza', 'bajo', 'correlacion', 'concentrado → ¿se mueven juntas las variables?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('varianza', 'bajo', 'persistencia', 'concentrado → ¿es estable o transitorio?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('skewness', 'bajo', 'var_parametrico', 'cola izquierda → ¿cuánto puedo perder?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('skewness', 'bajo', 'marco_amplificacion', 'cola izquierda → ¿hay espiral descendente?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('skewness', 'alto', 'elasticidad_general', 'cola derecha → ¿cuán sensible es al upside?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('kurtosis', 'alto', 'var_parametrico', 'colas pesadas → cuantificar el riesgo extremo')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('kurtosis', 'alto', 'garch', 'colas pesadas → ¿la volatilidad se autoalimenta?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('gini', 'alto', 'hhi', 'desigualdad alta → ¿está concentrado en pocos?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('gini', 'alto', 'marco_n_agentes', 'desigualdad alta → ¿cuántos jugadores dominan?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('correlacion', 'alto', 'elasticidad_general', 'co-movimiento fuerte → ¿cuán sensible?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('correlacion', 'alto', 'marco_cruce', 'co-movimiento → ¿hay equilibrio de Nash?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('correlacion', 'bajo', 'marco_n_componentes', 'independientes → ¿el sistema está fragmentado?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('correlacion', 'siempre', 'persistencia', 'toda correlación → ¿es estable en el tiempo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('elasticidad_general', 'alto', 'curva_phillips', 'hipersensible → ¿trade-off inflación/empleo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('elasticidad_general', 'bajo', 'regla_taylor', 'insensible → ¿la política monetaria funciona?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('persistencia', 'alto', 'marco_diagonal', 'persistente → ¿cuánta inercia secuencial?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('persistencia', 'alto', 'dyn_deuda', 'persistente → ¿es sostenible a largo plazo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('persistencia', 'bajo', 'marco_vel_media', 'transitorio → ¿a qué velocidad se disipa?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('output_gap', 'alto', 'curva_phillips', 'sobre potencial → ¿cuánta presión inflacionaria?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('output_gap', 'alto', 'regla_taylor', 'sobre potencial → ¿qué tipo de interés?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('output_gap', 'bajo', 'multiplicador_fiscal', 'bajo potencial → ¿cuánto efecto tiene el estímulo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('output_gap', 'bajo', 'marco_agujeros', 'bajo potencial → ¿qué falta?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('gap', 'alto', 'marco_curvatura_media', 'sobre tendencia → ¿está cambiando de dirección?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('gap', 'bajo', 'marco_desplazamiento', 'bajo tendencia → ¿cuánto se ha movido del inicio?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('curva_phillips', 'alto', 'regla_taylor', 'presión inflacionaria → ¿qué hacer con los tipos?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('curva_phillips', 'bajo', 'multiplicador_fiscal', 'sin presión → margen para estímulo fiscal')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('regla_taylor', 'alto', 'ecuacion_fisher', 'tipos altos → ¿cuál es el tipo real?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('regla_taylor', 'siempre', 'dyn_deuda', 'cualquier tipo → ¿es sostenible la deuda?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('multiplicador_fiscal', 'alto', 'deuda_pib', 'multiplicador alto → ¿hay margen fiscal?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('multiplicador_fiscal', 'bajo', 'marco_ratio_feedback', 'multiplicador bajo → ¿hay leakage/feedback?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('var_parametrico', 'alto', 'marco_amplificacion', 'riesgo alto → ¿se autoamplifica?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('var_parametrico', 'alto', 'prospect_value', 'riesgo alto → ¿cómo lo percibe la gente?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('garch', 'alto', 'marco_n_ciclos', 'volatilidad autoalimentada → ¿cuántos loops?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('garch', 'alto', 'marco_prof_ciclo', 'autoalimentada → ¿cuán profundos los loops?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_amplificacion', 'alto', 'marco_regulacion', 'espiral detectada → ¿hay freno?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_amplificacion', 'alto', 'marco_coherencia_dir', 'espiral → ¿en qué dirección va?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_regulacion', 'bajo', 'marco_ratio_feedback', 'sin freno → ¿domina la amplificación?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_n_agentes', 'alto', 'marco_simetria_juego', 'muchos agentes → ¿poder equilibrado?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_n_agentes', 'alto', 'marco_alternancia', 'muchos agentes → ¿hay tensión activa?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_simetria_juego', 'bajo', 'marco_cruce', 'asimétrico → ¿hay Nash?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_simetria_juego', 'alto', 'marco_completitud', 'simétrico → ¿se exploran todas las estrategias?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_cruce', 'alto', 'equilibrio_nash', 'cruce detectado → buscar Nash')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_emergencia', 'alto', 'marco_coherencia_sis', 'emergencia → ¿las partes son coherentes?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_agujeros', 'alto', 'marco_persistencia_topo', 'gaps → ¿son persistentes o temporales?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_agujeros', 'alto', 'marco_compacidad', 'gaps → ¿está dispersa la estructura?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_curvatura_media', 'alto', 'marco_curvatura_max', 'mucha curvatura → ¿hay giros bruscos?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_curvatura_media', 'alto', 'marco_torsion', 'mucha curvatura → ¿el ritmo es constante?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_curvatura_max', 'alto', 'marco_ratio_inflexion', 'giro brusco → ¿cuántos cambios de régimen?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_vel_media', 'alto', 'marco_aceleracion', 'rápido → ¿se acelera o frena?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_vel_media', 'alto', 'marco_bruscos', 'rápido → ¿hay shocks?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_vel_media', 'bajo', 'marco_desplazamiento', 'lento → ¿se movió algo o está parado?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('marco_aceleracion', 'alto', 'marco_coherencia_dir', 'acelerando → ¿hacia dónde?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('did', 'alto', 'iv_2sls', 'efecto DiD → ¿confirma con IV?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('did', 'siempre', 't_statistic', 'cualquier efecto → ¿es significativo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('ols', 'siempre', 't_statistic', 'estimación → ¿es significativo?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('ols', 'siempre', 'r_cuadrado', 'estimación → ¿cuánto explica?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('t_statistic', 'alto', 'p_valor', 'significativo → ¿cuán incompatible con H0?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('r_cuadrado', 'bajo', 'residuo_solow', 'explica poco → ¿qué falta?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('capm', 'siempre', 'sharpe', 'retorno esperado → ¿eficiencia riesgo/retorno?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('capm', 'siempre', 'beta_capm', 'retorno → ¿cuánta sensibilidad al mercado?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('sharpe', 'bajo', 'frontera_eficiente', 'mal compensado → ¿dónde está la frontera?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('valor_presente_neto', 'alto', 'tir', 'VPN positivo → ¿cuál es la TIR?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('valor_presente_neto', 'bajo', 'bellman', 'VPN negativo → ¿hay opción de esperar? (valor de la opción)')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('deuda_pib', 'alto', 'dyn_deuda', 'deuda alta → ¿trayectoria explosiva?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('dyn_deuda', 'alto', 'prima_riesgo_arrowpratt', 'deuda diverge → ¿cuánto riesgo percibe el mercado?')
ON CONFLICT DO NOTHING;
INSERT INTO red_preguntas (formula_origen, condicion, formula_destino, razon)
VALUES ('dyn_deuda', 'alto', 'marco_amplificacion', 'diverge → ¿hay espiral deuda-tipos?')
ON CONFLICT DO NOTHING;



-- Patrones históricos
DELETE FROM patrones_historicos;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('ESTANFLACION', 'Inflación persistente con estancamiento económico. La curva de Phillips colapsa.', '{"corr_inflacion_desempleo": [">", 0.3], "pib_crecimiento_medio": ["<", 0.01], "inflacion_momentum": [">", 0.1]}'::jsonb, ARRAY['UK 1970s','USA 1973-75','Brasil 2014-16'], 'Volcker shock (subida agresiva tipos) funcionó; gradualismo fracasó.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('TRAMPA_LIQUIDEZ', 'Tipos cerca de cero, política monetaria ineficaz. El dinero se acumula sin circular.', '{"tipo_interes_nivel": ["<", 1.0], "inflacion_momentum": ["<", -0.05], "elasticidad_consumo_tipo_interes": [">", -0.05]}'::jsonb, ARRAY['Japón 1990-2020','Eurozona 2014-19','USA 2008-15'], 'QE + estímulo fiscal masivo + forward guidance comprometido.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('BOOM_EXPORTADOR', 'Crecimiento liderado por exportaciones. Riesgo de dutch disease y dependencia externa.', '{"pib_crecimiento_medio": [">", 0.008], "exportaciones_momentum": [">", 0.1], "desempleo_momentum": ["<", -0.05]}'::jsonb, ARRAY['Alemania 2003-08','China 2001-08','Corea 1960-97'], 'Diversificar fuentes de crecimiento; crear fondos soberanos; invertir en capital humano.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('CRISIS_FISCAL', 'Espiral deuda-tipos: la deuda sube, los mercados exigen más interés, la deuda sube más.', '{"deuda_pib_momentum": [">", 0.1], "tipo_interes_momentum": [">", 0.1], "pib_crecimiento_medio": ["<", -0.005]}'::jsonb, ARRAY['Grecia 2010-15','Argentina 2001','Italia 2011'], 'Reestructuración + ajuste fiscal creíble + apoyo externo (FMI/BCE).')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('BURBUJA_ACTIVOS', 'Crecimiento alto con inflación baja oculta formación de burbuja en activos.', '{"pib_crecimiento_medio": [">", 0.01], "inflacion_nivel": ["<", 2.0], "inversion_momentum": [">", 0.15]}'::jsonb, ARRAY['USA 1995-2000 (dot-com)','USA 2003-07 (inmobiliaria)','Japón 1985-90'], 'Regulación macroprudencial; subida preventiva de tipos; vigilancia apalancamiento.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('DEFLACION_SECULAR', 'Deflación crónica con deuda masiva. El valor real de la deuda crece, deprimiendo inversión.', '{"inflacion_crecimiento_medio": ["<", -0.01], "tipo_interes_nivel": ["<", 0.5], "deuda_pib_nivel": [">", 200]}'::jsonb, ARRAY['Japón 1990-2020','Gran Depresión 1930-33'], 'Expansión fiscal masiva + QE permanente + reformas estructurales profundas.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('SUDDEN_STOP', 'Parada súbita de flujos de capital. Colapso de tipo de cambio y output.', '{"pib_tasa_cambio": ["<", -0.03], "importaciones_momentum": [">", 0.05]}'::jsonb, ARRAY['Asia 1997','Rusia 1998','Turquía 2018'], 'Control de capitales temporal + ajuste fiscal + acuerdo FMI.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;
INSERT INTO patrones_historicos (nombre, descripcion, señales, precedentes, prescripcion_historica)
VALUES ('AUSTERIDAD_CONTRAPRODUCENTE', 'El ajuste fiscal deprime tanto el PIB que la ratio deuda/PIB sube en vez de bajar.', '{"pib_crecimiento_medio": ["<", -0.002], "deuda_pib_momentum": [">", 0.02], "consumo_momentum": ["<", -0.05]}'::jsonb, ARRAY['Grecia 2010-14','España 2011-13','Portugal 2011-13'], 'Ajuste más gradual; priorizar crecimiento; reformas estructurales antes que recortes.')
ON CONFLICT (nombre) DO UPDATE SET
  descripcion=EXCLUDED.descripcion, señales=EXCLUDED.señales,
  precedentes=EXCLUDED.precedentes, prescripcion_historica=EXCLUDED.prescripcion_historica;