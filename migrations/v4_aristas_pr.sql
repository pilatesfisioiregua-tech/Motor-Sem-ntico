-- V4: Ampliar aristas_grafo para relaciones P↔P y R↔R

-- Quitar FK de inteligencias (P y R no están en esa tabla) — Opción A
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_origen_fkey;
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_destino_fkey;

-- Quitar restricción antigua y poner una más amplia
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_tipo_check;
ALTER TABLE aristas_grafo ADD CONSTRAINT aristas_grafo_tipo_check
    CHECK (tipo IN ('composicion', 'fusion', 'diferencial', 'redundancia',
                    'complementario_pp', 'validacion_rr'));

-- IC5: Pares complementarios P↔P (Maestro V4 §2.10)
INSERT INTO aristas_grafo (origen, destino, tipo, peso, hallazgo_emergente)
VALUES
    ('P06', 'P07', 'complementario_pp', 0.90, 'Ciclo generar/seleccionar — divergente + convergente'),
    ('P05', 'P04', 'complementario_pp', 0.85, 'Deconstruir/reconstruir — primeros principios + diseño'),
    ('P05', 'P11', 'complementario_pp', 0.80, 'Deconstruir/reconstruir — primeros principios + encarnado'),
    ('P08', 'P11', 'complementario_pp', 0.85, 'Pensar sobre pensar / actuar — metacognición + encarnado')
ON CONFLICT DO NOTHING;

-- IC6: Validación cruzada R↔R (Maestro V4 §2.11)
INSERT INTO aristas_grafo (origen, destino, tipo, peso, hallazgo_emergente)
VALUES
    ('R01', 'R02', 'validacion_rr', 0.85, 'Deducción sin inducción = premisas no validadas (Maginot)'),
    ('R01', 'R03', 'validacion_rr', 0.85, 'Deducción sin abducción = certeza sin diagnóstico'),
    ('R02', 'R06', 'validacion_rr', 0.80, 'Inducción sin contrafactual = generalización sin excepciones (cisne negro)'),
    ('R07', 'R08', 'validacion_rr', 0.80, 'Bayesiano sin dialéctico = priors fijos, echo chamber')
ON CONFLICT DO NOTHING;
