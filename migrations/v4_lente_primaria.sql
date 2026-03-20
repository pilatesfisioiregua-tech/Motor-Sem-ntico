-- V4 §2.3: Afinidad de lente por inteligencia
-- Generan S: INT-01, 02, 05, 07, 10, 11, 16
-- Generan Se: INT-03, 04, 06, 08, 09, 12, 14, 15, 17, 18
-- Generan C: INT-13 (+ secundarias: 02, 04, 12, 16, 18)

ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lente_primaria TEXT;
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lentes_secundarias TEXT[];

UPDATE inteligencias SET lente_primaria = 'S' WHERE id IN ('INT-01','INT-02','INT-05','INT-07','INT-10','INT-11','INT-16');
UPDATE inteligencias SET lente_primaria = 'Se' WHERE id IN ('INT-03','INT-04','INT-06','INT-08','INT-09','INT-12','INT-14','INT-15','INT-17','INT-18');
UPDATE inteligencias SET lente_primaria = 'C' WHERE id = 'INT-13';

-- Secundarias de C
UPDATE inteligencias SET lentes_secundarias = '{"C"}' WHERE id IN ('INT-02','INT-04','INT-12','INT-16','INT-18');
-- INT-13 ya tiene C como primaria, añadir S como secundaria
UPDATE inteligencias SET lentes_secundarias = '{"S"}' WHERE id = 'INT-13';
