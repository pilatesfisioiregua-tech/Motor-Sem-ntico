-- src/db/seed.sql

-- ═══ INTELIGENCIAS ═══
-- Incluye raices_dominio, modos_naturales, modos_forzados (v2)

INSERT INTO inteligencias (id, nombre, categoria, firma, punto_ciego, objetos_exclusivos, es_irreducible, raices_dominio, modos_naturales, modos_forzados, preguntas)
VALUES
('INT-01', 'Lógico-Matemática', 'Cuantitativa',
 'Contradicción formal demostrable entre premisas',
 'Lo ambiguo, lo no-axiomatizable',
 ARRAY['Ecuaciones', 'trade-offs irreducibles', 'sistemas subdeterminados'],
 TRUE,
 ARRAY['ecuacion', 'variable', 'contradiccion', 'limite', 'optimizacion'],
 ARRAY['analizar'],
 ARRAY['sentir', 'generar'],
 '{"extraer": "formalizar", "cruzar": "estructurar tipo de problema", "lentes": ["Álgebra", "Análisis", "Geometría", "Probabilidad", "Optimización", "Lógica"]}'::jsonb),

('INT-02', 'Computacional', 'Cuantitativa',
 'Dato trivializador ausente + atajo algorítmico',
 'Lo no-computable, la intuición',
 ARRAY['Grafos de dependencia', 'mutex', 'scheduling', 'complejidad'],
 TRUE,
 ARRAY['dato', 'algoritmo', 'dependencia', 'complejidad', 'paralelismo'],
 ARRAY['analizar', 'mover'],
 ARRAY['sentir'],
 '{"extraer": "descomponer", "cruzar": "clasificar complejidad", "lentes": ["Algorítmica", "Estructuras de datos", "Concurrencia", "Aproximación"]}'::jsonb),

('INT-03', 'Estructural (IAS)', 'Sistémica',
 'Gap id↔ir + actor invisible con poder',
 'No genera soluciones',
 ARRAY['Coordenadas sintácticas', 'circuitos causales', 'topología de poder'],
 FALSE,
 ARRAY['identidad', 'estructura', 'circuito', 'contenedor', 'control'],
 ARRAY['percibir', 'analizar'],
 ARRAY['generar'],
 '{"extraer": "mapear coordenadas", "cruzar": "buscar huecos activos", "lentes": ["Contenedores", "Circuitos", "Tablero", "Control"]}'::jsonb),

('INT-04', 'Ecológica', 'Sistémica',
 'Nichos vacíos + capital biológico en depreciación',
 'No ve al individuo',
 ARRAY['Monocultivo', 'resiliencia', 'ciclos de regeneración'],
 FALSE,
 ARRAY['nicho', 'resiliencia', 'diversidad', 'ciclo', 'flujo'],
 ARRAY['percibir'],
 ARRAY['mover'],
 '{"extraer": "mapear el ecosistema", "cruzar": "evaluar resiliencia", "lentes": ["Diversidad", "Flujos", "Resiliencia", "Ciclos"]}'::jsonb),

('INT-05', 'Estratégica', 'Posicional',
 'Secuencia obligatoria de movimientos + reversibilidad',
 'Asume competición',
 ARRAY['Opcionalidad', 'ventanas temporales', 'posición'],
 FALSE,
 ARRAY['posicion', 'movimiento', 'ventana', 'opcion', 'reversibilidad'],
 ARRAY['mover', 'analizar'],
 ARRAY['sentir'],
 '{"extraer": "evaluar posición", "cruzar": "secuenciar movimientos", "lentes": ["Posición", "Opcionalidad", "Timing", "Asimetría"]}'::jsonb),

('INT-06', 'Política', 'Posicional',
 'Poder como objeto + coaliciones no articuladas',
 'Confunde poder con verdad',
 ARRAY['Plebiscitos silenciosos', 'legitimidad', 'influencia espectral'],
 TRUE,
 ARRAY['poder', 'coalicion', 'legitimidad', 'narrativa', 'influencia'],
 ARRAY['enmarcar', 'mover'],
 ARRAY['sentir'],
 '{"extraer": "mapear poder", "cruzar": "analizar legitimidad", "lentes": ["Coaliciones", "Legitimidad", "Narrativa", "Influencia"]}'::jsonb),

('INT-07', 'Financiera', 'Cuantitativa',
 'Asimetría payoffs cuantificada + tasa de descuento invertida',
 'Lo sin precio no existe',
 ARRAY['VP', 'ratio fragilidad', 'margen de seguridad'],
 FALSE,
 ARRAY['flujo', 'riesgo', 'valor', 'margen', 'deuda', 'opcionalidad'],
 ARRAY['analizar'],
 ARRAY['sentir', 'generar'],
 '{"extraer": "mapear flujos", "cruzar": "evaluar riesgo", "lentes": ["Valor presente", "Apalancamiento", "Opcionalidad", "Margen de seguridad"]}'::jsonb),

('INT-08', 'Social', 'Interpretativa',
 'Vergüenza no nombrada + lealtad invisible',
 'Sobrepsicologiza',
 ARRAY['Duelo anticipado', 'identidad fusionada', 'queja cifrada'],
 TRUE,
 ARRAY['emocion', 'verguenza', 'lealtad', 'identidad', 'vinculo'],
 ARRAY['sentir', 'percibir'],
 ARRAY['analizar'],
 '{"extraer": "mapear emociones", "cruzar": "emociones × relaciones", "lentes": ["Empatía", "Patrones", "Vínculos", "Identidad"]}'::jsonb),

('INT-09', 'Lingüística', 'Interpretativa',
 'Palabra ausente + acto performativo',
 'Confunde nombrar con resolver',
 ARRAY['Marcos', 'silencios estratégicos', 'metáforas-prisión'],
 FALSE,
 ARRAY['marco', 'metafora', 'silencio', 'performativo', 'nombre'],
 ARRAY['enmarcar', 'percibir'],
 ARRAY['mover'],
 '{"extraer": "mapear lenguaje", "cruzar": "lenguaje × realidad", "lentes": ["Marcos", "Metáforas", "Actos de habla", "Silencios"]}'::jsonb),

('INT-10', 'Cinestésica', 'Corporal-Perceptual',
 'Tensión-nudo vs tensión-músculo + arritmia de tempos',
 'No verbaliza',
 ARRAY['Cascada somática', 'ritmo', 'coordinación corporal'],
 FALSE,
 ARRAY['tension', 'ritmo', 'coordinacion', 'flujo', 'cuerpo'],
 ARRAY['sentir', 'mover'],
 ARRAY['analizar', 'enmarcar'],
 '{"extraer": "mapear tensiones", "cruzar": "tensión × ritmo", "lentes": ["Tensión", "Ritmo", "Coordinación", "Flujo"]}'::jsonb),

('INT-11', 'Espacial', 'Espacial',
 'Punto de compresión + pendiente gravitacional',
 'Lo sin extensión no existe',
 ARRAY['Fronteras permeables', 'divergencia tri-perspectiva'],
 FALSE,
 ARRAY['espacio', 'compresion', 'frontera', 'perspectiva', 'proporcion'],
 ARRAY['percibir'],
 ARRAY['sentir'],
 '{"extraer": "mapear espacio", "cruzar": "perspectivas", "lentes": ["Compresión", "Perspectiva", "Frontera", "Proporción"]}'::jsonb),

('INT-12', 'Narrativa', 'Interpretativa',
 'Roles arquetípicos + narrativa autoconfirmante',
 'Fuerza protagonista',
 ARRAY['Arcos', 'Viaje del Héroe invertido', 'fantasma-espejo'],
 FALSE,
 ARRAY['arco', 'personaje', 'conflicto', 'significado', 'narrativa'],
 ARRAY['generar', 'percibir'],
 ARRAY['analizar'],
 '{"extraer": "identificar el arco", "cruzar": "narrativa × realidad", "lentes": ["Arco", "Personaje", "Conflicto", "Significado"]}'::jsonb),

('INT-13', 'Prospectiva', 'Expansiva',
 'Trampa de escalamiento sectorial + señales débiles',
 'El cisne negro',
 ARRAY['Escenarios', 'comodines', 'bifurcaciones'],
 FALSE,
 ARRAY['tendencia', 'escenario', 'señal', 'bifurcacion', 'comodin'],
 ARRAY['generar', 'percibir'],
 ARRAY['mover'],
 '{"extraer": "mapear futuros", "cruzar": "tendencias × disrupciones", "lentes": ["Tendencias", "Escenarios", "Señales", "Bifurcaciones"]}'::jsonb),

('INT-14', 'Divergente', 'Expansiva',
 '20+ opciones donde el sujeto ve 2',
 'No evalúa',
 ARRAY['Restricciones asumidas', 'inversiones radicales', 'acción mínima'],
 TRUE,
 ARRAY['opcion', 'restriccion', 'inversion', 'escala', 'eliminacion'],
 ARRAY['generar'],
 ARRAY['analizar'],
 '{"extraer": "ampliar opciones", "cruzar": "restricciones × posibilidades", "lentes": ["Inversión", "Combinación", "Escala", "Eliminación"]}'::jsonb),

('INT-15', 'Estética', 'Corporal-Perceptual',
 'Isomorfismo solución-problema + tristeza anticipatoria',
 'Lo feo puede ser verdadero',
 ARRAY['Disonancia formal', 'simetría generacional', 'reducción esencial'],
 FALSE,
 ARRAY['coherencia', 'isomorfismo', 'proporcion', 'esencia', 'disonancia'],
 ARRAY['percibir', 'sentir'],
 ARRAY['mover'],
 '{"extraer": "percibir forma", "cruzar": "forma × fondo", "lentes": ["Coherencia", "Isomorfismo", "Proporción", "Esencia"]}'::jsonb),

('INT-16', 'Constructiva', 'Operativa',
 'Prototipo con coste, secuencia y fallo seguro',
 'No cuestiona premisas',
 ARRAY['Camino crítico', 'versiones iterativas', 'rollback plan'],
 TRUE,
 ARRAY['prototipo', 'secuencia', 'coste', 'fallo', 'iteracion'],
 ARRAY['mover'],
 ARRAY['sentir', 'percibir'],
 '{"extraer": "identificar lo construible", "cruzar": "prototipo × restricciones", "lentes": ["Prototipo", "Secuencia", "Fallo seguro", "Iteración"]}'::jsonb),

('INT-17', 'Existencial', 'Contemplativa-Existencial',
 'Brecha valores declarados vs vividos + inercia como no-elección',
 'Puede paralizar',
 ARRAY['Propósito degradado', 'finitud', 'ventanas irrecuperables'],
 FALSE,
 ARRAY['valor', 'proposito', 'finitud', 'autenticidad', 'responsabilidad'],
 ARRAY['enmarcar', 'sentir'],
 ARRAY['mover'],
 '{"extraer": "mapear valores", "cruzar": "valores × acciones", "lentes": ["Propósito", "Finitud", "Responsabilidad", "Autenticidad"]}'::jsonb),

('INT-18', 'Contemplativa', 'Contemplativa-Existencial',
 'Urgencia inventada + vacío como recurso',
 'Puede desconectar de acción',
 ARRAY['Pausa como acto', 'paradoja sostenida', 'soltar'],
 FALSE,
 ARRAY['presencia', 'paradoja', 'vacio', 'pausa', 'soltar'],
 ARRAY['sentir'],
 ARRAY['analizar', 'mover'],
 '{"extraer": "observar sin juzgar", "cruzar": "observación × impulso", "lentes": ["Presencia", "Paradoja", "Soltar", "Vacío"]}'::jsonb)

ON CONFLICT (id) DO NOTHING;


-- ═══ ARISTAS — PARES DE MÁXIMO DIFERENCIAL ═══

INSERT INTO aristas_grafo (origen, destino, tipo, peso, direccion_optima, hallazgo_emergente) VALUES
-- TOP complementarios (score > 0.85)
('INT-01', 'INT-08', 'diferencial', 0.95, 'INT-01→INT-08', 'Coste financiero de la ruptura emocional. El debate ES la enfermedad.'),
('INT-07', 'INT-17', 'diferencial', 0.93, 'INT-07→INT-17', 'Precio de la autenticidad cuantificado. Espectro intermedio invisible.'),
('INT-02', 'INT-15', 'diferencial', 0.90, 'INT-02→INT-15', 'Dato trivializador + isomorfismo solución-problema.'),
('INT-09', 'INT-16', 'diferencial', 0.88, 'INT-09→INT-16', 'Marcos lingüísticos + prototipo construible con coste.'),
('INT-04', 'INT-14', 'diferencial', 0.87, 'INT-04→INT-14', 'Monocultivo + 20 opciones de reconfiguración.'),
('INT-06', 'INT-18', 'diferencial', 0.86, 'INT-06→INT-18', 'Coaliciones + urgencia inventada.'),
('INT-03', 'INT-18', 'diferencial', 0.84, 'INT-03→INT-18', 'Gap id↔ir + pausa como acto. Sillón vacío como bisagra.'),
('INT-05', 'INT-09', 'diferencial', 0.82, 'INT-05→INT-09', 'Secuencia obligatoria + metáfora-prisión.'),
('INT-02', 'INT-17', 'diferencial', 0.88, 'INT-02→INT-17', 'Optimización técnica como mecanismo de evitación existencial.'),
('INT-06', 'INT-16', 'diferencial', 0.85, 'INT-06→INT-16', 'Gobernanza como prototipo construible.'),
('INT-14', 'INT-01', 'diferencial', 0.86, 'INT-14→INT-01', 'Divergencia describe cambio de modelo sin reconocerlo.'),

-- Composiciones confirmadas (Fase 3)
('INT-01', 'INT-08', 'composicion', 0.92, 'INT-01→INT-08', 'El análisis racional replica la defensa psicológica.'),
('INT-02', 'INT-17', 'composicion', 0.90, 'INT-02→INT-17', 'Optimización técnica como evitación existencial.'),
('INT-06', 'INT-16', 'composicion', 0.88, 'INT-06→INT-16', 'Gobernanza construible: 2 semanas, 0€, datos churn como zona desmilitarizada.'),
('INT-14', 'INT-01', 'composicion', 0.85, 'INT-14→INT-01', 'Divergencia sin filtro revela cambio total inadvertido.'),

-- Fusiones confirmadas (Fase 3)
('INT-01', 'INT-08', 'fusion', 0.95, NULL, 'Coste financiero de la ruptura emocional: 14% runway/mes.'),
('INT-06', 'INT-16', 'fusion', 0.88, NULL, 'Propuesta premium es zona de acuerdo política.'),
('INT-07', 'INT-17', 'fusion', 0.93, NULL, 'Precio autenticidad = 30-50K€/año, no 125K€.'),
('INT-03', 'INT-18', 'fusion', 0.84, NULL, 'Sillón vacío: optimización operativa + recuperación existencial.'),
('INT-07', 'INT-14', 'fusion', 0.82, NULL, 'VP da falsa certeza al marco binario.'),

-- Clusters de redundancia
('INT-03', 'INT-04', 'redundancia', 0.35, NULL, 'Ambas ven sistema completo.'),
('INT-03', 'INT-10', 'redundancia', 0.40, NULL, 'Ambas ven partes conectadas.'),
('INT-04', 'INT-10', 'redundancia', 0.38, NULL, 'Sistémicas: solapan 50-75%.'),
('INT-08', 'INT-12', 'redundancia', 0.40, NULL, 'Dimensión humana del drama.'),
('INT-17', 'INT-18', 'redundancia', 0.35, NULL, 'Significado profundo.'),
('INT-09', 'INT-15', 'redundancia', 0.40, NULL, 'Incongruencias de forma.')

ON CONFLICT (origen, destino, tipo) DO NOTHING;


-- ═══ MARCO LINGÜÍSTICO — 8 OPERACIONES SINTÁCTICAS ═══

INSERT INTO operaciones_sintacticas (nombre, input_tipo, output_tipo, propiedad_clave, pregunta_detectora, propiedades_algebraicas)
VALUES
('modificacion', 'adj + sust', 'sust''', 'filtra/especifica', '¿Cómo es?', '{"idempotente_mismo_adj": true, "apilable_distintos": true}'::jsonb),
('predicacion', 'sust + verbo', 'oracion', 'genera valor de verdad', '¿Qué hace? ¿En qué estado está?', '{"conmutativa": false}'::jsonb),
('complementacion', 'adv + verbo', 'verbo''', 'instrumento/modo', '¿Con qué? ¿Cómo?', '{}'::jsonb),
('transitividad', 'verbo + sust', 'predicado', 'objeto de la acción', '¿Sobre qué actúa?', '{"verbo_sin_objeto": "hueco"}'::jsonb),
('subordinacion', 'oracion + oracion', 'oracion''', 'causa/condicion/creencia', '¿Porque qué? ¿Si qué? ¿Qué asume?', '{"conmutativa_porque": false}'::jsonb),
('cuantificacion', 'det + sust', 'sust_acotado', 'alcance/límites', '¿Cuánto? ¿Todo o alguno?', '{}'::jsonb),
('conexion', 'X + conj + X', 'X''', 'tipo de acople', '¿Y/Pero/Aunque/Porque/Si/Para?', '{"Y_conmutativa": true, "PERO_no_asociativa": true}'::jsonb),
('transformacion', 'X', 'Y', 'cambio de categoría', '¿Qué era antes? ¿En qué se convierte?', '{"no_involutiva": true}'::jsonb)
ON CONFLICT (nombre) DO NOTHING;


-- ═══ 9 CAPAS DEL SISTEMA ═══

INSERT INTO capas_sistema (nombre, categoria_gramatical, pregunta, verbo_existencial, operacion_primaria)
VALUES
('lentes', 'Atributo de estado', '¿En qué estado está?', 'ESTAR', 'predicacion'),
('cualidades', 'Adjetivo predicativo', '¿Cómo es?', 'SER', 'modificacion'),
('creencias', 'Subordinada asertiva', '¿Qué asume?', 'ASUMIR', 'subordinacion'),
('reglas', 'Modal deóntico', '¿Qué debe hacer?', 'DEBER', 'subordinacion'),
('funciones', 'Verbo de acción', '¿Qué hace?', 'HACER', 'predicacion'),
('operadores', 'Complemento circunstancial', '¿Con qué observa?', 'OBSERVAR', 'complementacion'),
('contexto', 'Circunstancial lugar/tiempo', '¿Dónde/cuándo opera?', NULL, 'complementacion'),
('roles', 'Pronombre/deíctico', '¿Quién hace qué?', NULL, 'transitividad'),
('acoples', 'Conjunción', '¿Cómo se vinculan las piezas?', NULL, 'conexion')
ON CONFLICT (nombre) DO NOTHING;


-- ═══ 6 TIPOS DE ACOPLE ═══

INSERT INTO tipos_acople (conjuncion, tipo, diagnostico)
VALUES
('Y', 'sinergia', 'Ambas operan juntas — salud'),
('PERO', 'tension', 'Una limita a la otra — fricción activa'),
('AUNQUE', 'concesion', 'Tolera algo que no debería — grieta'),
('PORQUE', 'causalidad', 'Dependencia dirigida — cadena causal'),
('SI', 'condicionalidad', 'Requiere condición — fragilidad'),
('PARA', 'finalidad', 'Orientación — dirección')
ON CONFLICT (conjuncion) DO NOTHING;


-- ═══ FALACIAS ARITMÉTICAS ═══

INSERT INTO falacias_aritmeticas (nombre, operacion_incorrecta, correccion, ejemplo)
VALUES
('conducta_valor', 'Predicación tratada como Modificación', 'Pred → Sub_asertiva → Mod', 'Decir "es innovador" cuando hace cosas innovadoras'),
('optimizacion_sin_finalidad', 'Transformación sin Subordinación final', 'Tr + Sub_final(PARA qué)', 'Optimizar sin saber para qué'),
('friccion_es_fallo', 'Conexión PERO asumida como error', 'Evaluar si PERO es funcional', 'Asumir que toda tensión es mala'),
('creencia_como_regla', 'Sub_asertiva confundida con Sub_deóntica', 'Distinguir "creo que X" de "X debe ser"', 'Tratar opinión como obligación'),
('cualidad_como_funcion', 'Modificación confundida con Predicación', '"Es innovador" ≠ "innova"', 'Confundir ser con hacer'),
('verbo_sin_objeto', 'Predicación sin Transitividad', 'Función declarada pero no definida', '"Lidera" — ¿a quién? ¿hacia dónde?')
ON CONFLICT (nombre) DO NOTHING;
