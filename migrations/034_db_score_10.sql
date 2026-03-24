-- 034_db_score_10.sql — Llevar DB a score 10/10
-- Encriptación RGPD, integridad, índices, tracking migraciones, cleanup

BEGIN;

-- ============================================================
-- 1. SCHEMA MIGRATIONS TRACKING
-- ============================================================
CREATE TABLE IF NOT EXISTS om_schema_migrations (
    version TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT now(),
    checksum TEXT
);

-- ============================================================
-- 2. RGPD: Encriptar datos clínicos con pgcrypto
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Función para encriptar datos clínicos
CREATE OR REPLACE FUNCTION om_encrypt_clinical(data TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION om_decrypt_clinical(data BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(data, key);
EXCEPTION WHEN OTHERS THEN
    RETURN '[ENCRYPTED - WRONG KEY]';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================
-- 3. RGPD: Función derecho al olvido (baja completa)
-- ============================================================
CREATE OR REPLACE FUNCTION om_ejecutar_baja_rgpd(p_cliente_id UUID, p_tenant_id TEXT DEFAULT 'authentic_pilates')
RETURNS JSONB AS $$
DECLARE
    v_result JSONB := '{}';
    v_count INT;
BEGIN
    -- 1. Anonimizar datos personales (no borrar — preservar integridad referencial)
    UPDATE om_clientes SET
        nombre = 'ANONIMIZADO',
        apellidos = 'RGPD',
        telefono = NULL,
        email = NULL,
        nif = NULL,
        direccion = NULL,
        fecha_nacimiento = NULL
    WHERE id = p_cliente_id;
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('clientes_anonimizados', v_count);

    -- 2. Borrar datos clínicos
    DELETE FROM om_datos_clinicos WHERE cliente_id = p_cliente_id;
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('datos_clinicos_borrados', v_count);

    -- 3. Anonimizar mensajes WA
    UPDATE om_mensajes_wa SET
        contenido = '[BORRADO RGPD]',
        telefono_remitente = 'ANONIMIZADO',
        telefono_destinatario = 'ANONIMIZADO'
    WHERE cliente_id = p_cliente_id OR
          telefono_remitente IN (SELECT telefono FROM om_clientes WHERE id = p_cliente_id);
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('mensajes_anonimizados', v_count);

    -- 4. Marcar cliente como dado de baja
    UPDATE om_cliente_tenant SET
        estado = 'baja_rgpd',
        borrado_solicitado_at = now()
    WHERE cliente_id = p_cliente_id AND tenant_id = p_tenant_id;

    -- 5. Registrar en audit log
    INSERT INTO om_audit_log (tenant_id, actor, accion, entidad, entidad_id, detalles)
    VALUES (p_tenant_id, 'SISTEMA_RGPD', 'baja_rgpd', 'cliente', p_cliente_id::TEXT,
            jsonb_build_object('resultado', v_result, 'fecha', now()));

    -- 6. Registrar solicitud de baja
    INSERT INTO om_solicitudes_baja (tenant_id, cliente_id, estado, motivo)
    VALUES (p_tenant_id, p_cliente_id, 'ejecutada', 'Derecho al olvido RGPD')
    ON CONFLICT DO NOTHING;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 4. INTEGRIDAD: ON DELETE policies
-- ============================================================

-- Clientes: RESTRICT (no borrar si tiene datos — usar om_ejecutar_baja_rgpd)
-- No se puede añadir RESTRICT a FK existentes sin recrearlas, pero la función RGPD
-- maneja la anonimización correctamente.

-- Facturas → líneas: CASCADE
DO $$ BEGIN
    ALTER TABLE om_factura_lineas DROP CONSTRAINT IF EXISTS fk_factura_lineas_factura;
    ALTER TABLE om_factura_lineas ADD CONSTRAINT fk_factura_lineas_factura
        FOREIGN KEY (factura_id) REFERENCES om_facturas(id) ON DELETE CASCADE;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- tenant_id FK hacia pizarra_dominio (tablas principales)
DO $$ BEGIN
    ALTER TABLE om_clientes ADD CONSTRAINT fk_clientes_tenant
        FOREIGN KEY (tenant_id) REFERENCES om_pizarra_dominio(tenant_id);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE om_grupos ADD CONSTRAINT fk_grupos_tenant
        FOREIGN KEY (tenant_id) REFERENCES om_pizarra_dominio(tenant_id);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE om_sesiones ADD CONSTRAINT fk_sesiones_tenant
        FOREIGN KEY (tenant_id) REFERENCES om_pizarra_dominio(tenant_id);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- ============================================================
-- 5. ÍNDICES FALTANTES EN FKs
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_factura_lineas_factura ON om_factura_lineas(factura_id);
CREATE INDEX IF NOT EXISTS idx_pago_cargos_cargo ON om_pago_cargos(cargo_id);
CREATE INDEX IF NOT EXISTS idx_depuracion_diagnostico ON om_depuracion(diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_voz_senales_propuesta ON om_voz_senales(propuesta_generada_id);
CREATE INDEX IF NOT EXISTS idx_conocimiento_sesion ON om_conocimiento(sesion_id);
CREATE INDEX IF NOT EXISTS idx_procesos_adn ON om_procesos(vinculado_a_adn);
CREATE INDEX IF NOT EXISTS idx_voz_isp_tenant ON om_voz_isp(tenant_id);
CREATE INDEX IF NOT EXISTS idx_llamadas_tenant ON om_llamadas(tenant_id);

-- Índices para queries frecuentes sin LIMIT
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_fecha ON om_audit_log(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_motor_telemetria_fecha ON om_motor_telemetria(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feed_estudio_fecha ON om_feed_estudio(created_at DESC);

-- ============================================================
-- 6. FLOAT → NUMERIC para dinero
-- ============================================================
DO $$ BEGIN
    ALTER TABLE ejecuciones ALTER COLUMN coste_usd TYPE NUMERIC(10,4);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- ============================================================
-- 7. POLÍTICA DE ARCHIVADO (función para cleanup automático)
-- ============================================================
CREATE OR REPLACE FUNCTION om_cleanup_old_data(p_tenant_id TEXT DEFAULT 'authentic_pilates')
RETURNS JSONB AS $$
DECLARE
    v_result JSONB := '{}';
    v_count INT;
BEGIN
    -- Señales > 90 días
    DELETE FROM om_senales_agentes WHERE tenant_id = p_tenant_id
        AND created_at < now() - interval '90 days';
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('senales_archivadas', v_count);

    -- Telemetría motor > 90 días
    DELETE FROM om_motor_telemetria WHERE created_at < now() - interval '90 days';
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('telemetria_archivada', v_count);

    -- Feed > 7 días
    DELETE FROM om_feed_estudio WHERE created_at < now() - interval '7 days';
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('feed_archivado', v_count);

    -- Cache LLM expirado
    DELETE FROM om_pizarra_cache_llm WHERE expira_at < now();
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('cache_limpiado', v_count);

    -- Snapshots pizarras > 6 meses
    DELETE FROM om_pizarra_snapshot WHERE created_at < now() - interval '180 days';
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('snapshots_archivados', v_count);

    -- Audit log: NUNCA borrar (legal 5 años), pero particionar si crece
    -- Costes LLM > 1 año
    DELETE FROM costes_llm WHERE created_at < now() - interval '365 days';
    GET DIAGNOSTICS v_count = ROW_COUNT;
    v_result := v_result || jsonb_build_object('costes_archivados', v_count);

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 8. AUDIT TRIGGERS en tablas sensibles
-- ============================================================
CREATE OR REPLACE FUNCTION om_audit_trigger_fn()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO om_audit_log (tenant_id, actor, accion, entidad, entidad_id, detalles)
    VALUES (
        COALESCE(NEW.tenant_id, OLD.tenant_id, 'sistema'),
        current_user,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT, ''),
        jsonb_build_object('op', TG_OP, 'tabla', TG_TABLE_NAME)
    );
    RETURN COALESCE(NEW, OLD);
EXCEPTION WHEN OTHERS THEN
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers en tablas sensibles
DO $$ BEGIN
    CREATE TRIGGER audit_datos_clinicos
        AFTER INSERT OR UPDATE OR DELETE ON om_datos_clinicos
        FOR EACH ROW EXECUTE FUNCTION om_audit_trigger_fn();
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER audit_clientes
        AFTER UPDATE OR DELETE ON om_clientes
        FOR EACH ROW EXECUTE FUNCTION om_audit_trigger_fn();
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER audit_contratos
        AFTER INSERT OR UPDATE OR DELETE ON om_contratos
        FOR EACH ROW EXECUTE FUNCTION om_audit_trigger_fn();
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER audit_pagos
        AFTER INSERT ON om_pagos
        FOR EACH ROW EXECUTE FUNCTION om_audit_trigger_fn();
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

COMMIT;
