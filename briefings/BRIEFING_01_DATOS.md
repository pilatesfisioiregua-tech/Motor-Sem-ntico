# BRIEFING_01 — BASE DE DATOS Y DATOS SEMILLA

**Objetivo:** Schema SQL, seed con 18 inteligencias + aristas del grafo, inteligencias.json con redes de preguntas, cliente DB.
**Pre-requisito:** BRIEFING_00 completado.
**Output:** DB lista para el motor. inteligencias.json cargable en memoria.

---

## TAREA

1. Crear `src/db/schema.sql` — tablas: inteligencias, aristas_grafo, operaciones_sintacticas, capas_sistema, tipos_acople, falacias_aritmeticas, sufijos_operaciones, ejecuciones, embeddings_inteligencias
2. Crear `src/db/seed.sql` — INSERT de 18 inteligencias (con raices_dominio, modos_naturales, modos_forzados) + aristas del grafo + 8 operaciones + 9 capas + 6 acoples + 6 falacias
3. Crear `src/meta_red/inteligencias.json` — las 18 redes de preguntas completas
4. Crear `src/meta_red/marco_linguistico.json` — 8 operaciones, 9 capas, 6 acoples, 6 falacias (para Capa 0 y Capa 5)
5. Crear `src/db/client.py` — pool asyncpg + helpers
6. Crear `scripts/seed_db.py` — script para poblar DB

---

## 1. SCHEMA SQL

```sql
-- src/db/schema.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- INTELIGENCIAS Y META-RED
-- ==========================================

CREATE TABLE IF NOT EXISTS inteligencias (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    firma TEXT NOT NULL,
    punto_ciego TEXT NOT NULL,
    objetos_exclusivos TEXT[],
    es_irreducible BOOLEAN DEFAULT FALSE,
    raices_dominio TEXT[],            -- [v2] raíces pre-categoriales de esta inteligencia
    preguntas JSONB NOT NULL,
    modos_naturales TEXT[],           -- [v2] modos donde opera bien: ['analizar','percibir',...]
    modos_forzados TEXT[]             -- [v2] modos donde opera mal
);

-- Aristas del grafo de complementariedad
CREATE TABLE IF NOT EXISTS aristas_grafo (
    id SERIAL PRIMARY KEY,
    origen TEXT REFERENCES inteligencias(id),
    destino TEXT REFERENCES inteligencias(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('composicion', 'fusion', 'diferencial', 'redundancia')),
    peso FLOAT NOT NULL,
    direccion_optima TEXT,
    hallazgo_emergente TEXT,
    UNIQUE(origen, destino, tipo)
);

-- ==========================================
-- MARCO LINGÜÍSTICO (datos operativos)
-- ==========================================

-- Las 8 operaciones primitivas
CREATE TABLE IF NOT EXISTS operaciones_sintacticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    input_tipo TEXT NOT NULL,
    output_tipo TEXT NOT NULL,
    propiedad_clave TEXT NOT NULL,
    pregunta_detectora TEXT NOT NULL,
    propiedades_algebraicas JSONB
);

-- Las 9 capas del sistema (constituyentes sintácticos)
CREATE TABLE IF NOT EXISTS capas_sistema (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    categoria_gramatical TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    verbo_existencial TEXT,
    operacion_primaria TEXT
);

-- Los 6 tipos de acople
CREATE TABLE IF NOT EXISTS tipos_acople (
    id SERIAL PRIMARY KEY,
    conjuncion TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    diagnostico TEXT NOT NULL
);

-- Falacias aritméticas (errores de tipo lógico)
CREATE TABLE IF NOT EXISTS falacias_aritmeticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    operacion_incorrecta TEXT NOT NULL,
    correccion TEXT NOT NULL,
    ejemplo TEXT
);

-- Mapeo sufijo → operación → capa (para Capa 0)
CREATE TABLE IF NOT EXISTS sufijos_operaciones (
    id SERIAL PRIMARY KEY,
    sufijo TEXT NOT NULL,
    transforma_en TEXT NOT NULL,
    capa_destino TEXT
);

-- ==========================================
-- TELEMETRÍA Y RETROALIMENTACIÓN
-- ==========================================

CREATE TABLE IF NOT EXISTS ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    huecos_detectados JSONB,          -- [v2] output de Capa 0
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,        -- [v2] falacias encontradas por Capa 5
    feedback_usuario JSONB
);

-- Vectores para router futuro (pgvector)
CREATE TABLE IF NOT EXISTS embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_aristas_origen ON aristas_grafo(origen);
CREATE INDEX IF NOT EXISTS idx_aristas_destino ON aristas_grafo(destino);
CREATE INDEX IF NOT EXISTS idx_aristas_tipo ON aristas_grafo(tipo);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_modo ON ejecuciones(modo);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_created ON ejecuciones(created_at DESC);
```

---

## 2. SEED SQL — 18 INTELIGENCIAS

Usar estos datos exactos. Son derivados empíricamente de 34 chats de cartografía.

```sql
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
```

---

## 3. inteligencias.json

Este archivo contiene las redes COMPLETAS de preguntas de cada inteligencia. Es el corazón del motor.

**IMPORTANTE:** Las preguntas están en el documento adjunto (el PROMPT MVP, sección 6). Copiar TODAS las preguntas exactas, organizadas así:

```json
{
  "INT-01": {
    "id": "INT-01",
    "nombre": "Lógico-Matemática",
    "categoria": "Cuantitativa",
    "firma": "Contradicción formal demostrable entre premisas",
    "punto_ciego": "Lo ambiguo, lo no-axiomatizable",
    "meta_red": {
      "extraer": {
        "nombre": "formalizar",
        "preguntas": [
          "¿Qué se puede contar? ¿Qué se puede medir?",
          "¿Qué magnitudes aparecen con número explícito?",
          "¿Qué magnitudes aparecen sin número pero se podrían medir?",
          "¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?",
          "¿Qué se quiere saber que aún no se sabe?",
          "¿Qué se da por hecho sin verificar?"
        ]
      },
      "cruzar": {
        "nombre": "estructurar tipo de problema",
        "preguntas": [
          "De todas las relaciones, ¿cuántas puedes mover y cuántas están fijadas?",
          "¿Mover una variable mejora todo, o mejorar una empeora otra?",
          "Si empeora otra: ¿hay punto donde ambas sean aceptables, o siempre hay que elegir?",
          "¿Los números son continuos o discretos?",
          "¿Lo que no se sabe se puede estimar, o es genuinamente incierto?"
        ]
      },
      "lentes": [
        {
          "id": "L1",
          "nombre": "Álgebra",
          "preguntas": [
            "¿Cuántas ecuaciones hay y cuántas incógnitas?",
            "¿Alguna es redundante?",
            "¿Alguna contradice a otra?"
          ]
        },
        {
          "id": "L2",
          "nombre": "Análisis",
          "preguntas": [
            "Si aumentas cada variable un poco, ¿qué pasa?",
            "¿Hay punto donde aumentar empieza a empeorar?",
            "¿Alguna variable tiene efecto desproporcionado?"
          ]
        },
        {
          "id": "L3",
          "nombre": "Geometría",
          "preguntas": [
            "Si dibujas las opciones como puntos, ¿qué forma tienen?",
            "¿Las opciones buenas están concentradas o dispersas?"
          ]
        },
        {
          "id": "L4",
          "nombre": "Probabilidad",
          "preguntas": [
            "¿Qué números son seguros y cuáles estimaciones?",
            "¿Qué pasaría si los estimados se desvían un 20%?"
          ]
        },
        {
          "id": "L5",
          "nombre": "Optimización",
          "preguntas": [
            "¿Se puede mejorar todo a la vez?",
            "Si hay que elegir, ¿qué importa más — y quién decide eso?"
          ]
        },
        {
          "id": "L6",
          "nombre": "Lógica",
          "preguntas": [
            "¿Qué se puede deducir con certeza?",
            "¿Hay combinación de premisas que se contradiga?"
          ]
        }
      ],
      "integrar": "¿Qué dicen todas las lentes que coincide? ¿Dónde se contradicen? ¿Hay algo que solo aparece al mirar todas juntas?",
      "abstraer": "¿Este caso es único o hay una clase de casos que comparten esta estructura? Si quitas nombres y números, ¿qué patrón queda?",
      "frontera": "¿Qué asume este análisis que no ha examinado? ¿Hay algo que no se puede expresar como número o ecuación? Si eso fuera lo más importante, ¿qué cambia?"
    }
  }
}
```

**Repetir esta estructura para las 18 inteligencias.** Las preguntas completas de CADA una están en la sección 6 del PROMPT MVP (el documento que se te proporcionó como contexto del proyecto). Copia TODAS las preguntas exactas de cada paso (EXTRAER, CRUZAR, cada LENTE, INTEGRAR, ABSTRAER, FRONTERA) para las 18 inteligencias.

NO inventar preguntas. NO resumir. Copiar literal de la sección 6 del prompt.

---

## 4. DB CLIENT

```python
# src/db/client.py
"""Pool de conexiones asyncpg para Postgres."""
import asyncpg
import structlog
from src.config.settings import DATABASE_URL

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        log.info("db_pool_created")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("db_pool_closed")


async def execute_schema():
    """Ejecuta schema.sql para crear tablas."""
    pool = await get_pool()
    import importlib.resources as pkg_resources
    from pathlib import Path
    schema_path = Path(__file__).parent / "schema.sql"
    schema = schema_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(schema)
    log.info("schema_executed")


async def execute_seed():
    """Ejecuta seed.sql para poblar datos."""
    pool = await get_pool()
    from pathlib import Path
    seed_path = Path(__file__).parent / "seed.sql"
    seed = seed_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(seed)
    log.info("seed_executed")


async def fetch_all_inteligencias() -> list[dict]:
    """Carga todas las inteligencias de la DB."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM inteligencias ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_aristas(tipo: str | None = None) -> list[dict]:
    """Carga aristas del grafo. Filtra por tipo si se indica."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tipo:
            rows = await conn.fetch(
                "SELECT * FROM aristas_grafo WHERE tipo = $1 ORDER BY peso DESC",
                tipo
            )
        else:
            rows = await conn.fetch("SELECT * FROM aristas_grafo ORDER BY peso DESC")
        return [dict(r) for r in rows]


async def log_ejecucion(data: dict) -> str:
    """Guarda una ejecución y devuelve su UUID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO ejecuciones (input, contexto, modo, huecos_detectados, algoritmo_usado, resultado, coste_usd, tiempo_s, score_calidad, falacias_detectadas)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8, $9, $10::jsonb)
            RETURNING id
        """, data['input'], data.get('contexto'), data['modo'],
            data.get('huecos_detectados'), data['algoritmo_usado'], data['resultado'],
            data.get('coste_usd'), data.get('tiempo_s'), data.get('score_calidad'),
            data.get('falacias_detectadas'))
        return str(row['id'])


async def fetch_operaciones_sintacticas() -> list[dict]:
    """Carga las 8 operaciones del Marco Lingüístico."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM operaciones_sintacticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_falacias() -> list[dict]:
    """Carga las falacias aritméticas."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM falacias_aritmeticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_tipos_acople() -> list[dict]:
    """Carga los 6 tipos de acople."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tipos_acople ORDER BY id")
        return [dict(r) for r in rows]
```

---

## 5. SEED SCRIPT

```python
# scripts/seed_db.py
"""Ejecuta schema + seed en la DB."""
import asyncio
import sys
sys.path.insert(0, '.')
from src.db.client import execute_schema, execute_seed, close_pool

async def main():
    print("Ejecutando schema...")
    await execute_schema()
    print("Ejecutando seed...")
    await execute_seed()
    print("Done.")
    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## VERIFICACIÓN

1. Con DATABASE_URL configurada: `python scripts/seed_db.py` debe completar sin error
2. `psql $DATABASE_URL -c "SELECT id, nombre FROM inteligencias ORDER BY id"` debe mostrar 18 filas
3. `psql $DATABASE_URL -c "SELECT COUNT(*) FROM aristas_grafo"` debe mostrar ~27 aristas
4. `psql $DATABASE_URL -c "SELECT COUNT(*) FROM operaciones_sintacticas"` debe mostrar 8
5. `psql $DATABASE_URL -c "SELECT COUNT(*) FROM falacias_aritmeticas"` debe mostrar 6
6. `python -c "import json; d=json.load(open('src/meta_red/inteligencias.json')); print(len(d))"` debe imprimir 18
7. `python -c "import json; d=json.load(open('src/meta_red/marco_linguistico.json')); print(list(d.keys()))"` debe imprimir las 4 secciones
