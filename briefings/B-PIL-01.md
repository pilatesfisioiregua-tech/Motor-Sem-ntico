# B-PIL-01: Schema SQL Pilates — 29 tablas om_* en fly.io Postgres

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** Ninguna (B-ACD-19 Fase A debe estar desplegada para que execute_migrations funcione)
**Coste:** $0 (solo DDL)

---

## CONTEXTO

El Exocortex Pilates v2.1 define 29 tablas con prefijo `om_` que conviven en la misma DB Postgres de fly.io donde ya viven las tablas del Motor vN (inteligencias, ejecuciones, diagnosticos, etc.). El sistema `execute_migrations()` ya corre en startup y ejecuta todos los `.sql` de `migrations/`. Solo hay que crear el archivo SQL.

**Fuente de verdad:** `docs/producto/casos/pilates/EXOCORTEX_PILATES_DEFINITIVO_v2.1.md` sección S3.

---

## FASE ÚNICA: Crear migración SQL

### 1. Crear archivo `migrations/om_pilates_schema.sql`

**IMPORTANTE:** Todas las sentencias deben ser idempotentes (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). El archivo se ejecuta en cada deploy.

**IMPORTANTE:** Hay dependencias de orden entre tablas (FKs). El orden correcto es:
1. om_clientes (sin FK)
2. om_grupos (sin FK a otras om_*)
3. om_contratos (FK → om_clientes, om_grupos)
4. om_sesiones (FK → om_grupos)
5. om_asistencias (FK → om_sesiones, om_clientes, om_contratos)
6. om_cargos (FK → om_clientes, om_contratos, om_sesiones, om_asistencias)
7. om_pagos (FK → om_clientes)
8. om_pago_cargos (FK → om_pagos, om_cargos)
9. om_facturas (FK → om_clientes)
10. om_factura_lineas (FK → om_facturas, om_cargos)
11. om_gastos (sin FK)
12. om_voz_propuestas (sin FK)
13. om_voz_telemetria (sin FK)
14. om_voz_isp (sin FK)
15. om_voz_capa_a (sin FK)
16. om_mensajes_wa (FK → om_clientes)
17. om_llamadas (FK → om_clientes)
18. om_adn (sin FK)
19. om_procesos (FK → om_adn)
20. om_conocimiento (FK → om_sesiones, om_adn)
21. om_onboarding_instructor (sin FK)
22. om_tensiones (sin FK)
23. om_sesiones_consejo (sin FK)
24. om_dias_esperados (FK → om_contratos, om_clientes, om_grupos)
25. om_cliente_tenant (FK → om_clientes)
26. om_datos_clinicos (FK → om_clientes)
27. om_onboarding_links (FK → om_clientes)
28. om_diagnosticos_tenant (FK → om_sesiones_consejo)
29. om_depuracion (FK → om_diagnosticos_tenant)

Contenido completo del archivo SQL — **COPIAR TAL CUAL:**

```sql
-- ============================================================
-- EXOCORTEX PILATES — Schema v2.1
-- 29 tablas om_* — Idempotente (IF NOT EXISTS)
-- Fuente: EXOCORTEX_PILATES_DEFINITIVO_v2.1.md S3
-- ============================================================

-- BLOQUE 1: GESTION (11 tablas)

CREATE TABLE IF NOT EXISTS om_clientes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  apellidos TEXT NOT NULL,
  telefono TEXT,
  email TEXT,
  fecha_nacimiento DATE,
  nif TEXT,
  direccion TEXT,
  metodo_pago_habitual TEXT CHECK (metodo_pago_habitual IN ('tpv', 'bizum', 'efectivo', 'transferencia')),
  metodo_pago_confianza NUMERIC(3,2) DEFAULT 0,
  consentimiento_datos BOOLEAN DEFAULT false,
  consentimiento_marketing BOOLEAN DEFAULT false,
  consentimiento_compartir_tenants BOOLEAN DEFAULT false,
  fecha_consentimiento TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_grupos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  nombre TEXT NOT NULL,
  tipo TEXT NOT NULL DEFAULT 'estandar' CHECK (tipo IN ('estandar', 'mat')),
  capacidad_max INT NOT NULL,
  dias_semana JSONB NOT NULL,
  precio_mensual NUMERIC(6,2) NOT NULL,
  frecuencia_semanal INT NOT NULL DEFAULT 2,
  instructor TEXT NOT NULL DEFAULT 'Jesus',
  estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'migrando')),
  migra_a UUID REFERENCES om_grupos(id),
  migra_fecha DATE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_contratos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('individual', 'grupo')),
  frecuencia_semanal INT,
  precio_sesion NUMERIC(6,2),
  ciclo_cobro TEXT CHECK (ciclo_cobro IN ('sesion', 'semanal', 'mensual')),
  grupo_id UUID REFERENCES om_grupos(id),
  precio_mensual NUMERIC(6,2),
  dia_fijo INT,
  estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'pausa', 'cancelado')),
  fecha_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin DATE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_sesiones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('individual', 'grupo')),
  grupo_id UUID REFERENCES om_grupos(id),
  instructor TEXT NOT NULL DEFAULT 'Jesus',
  fecha DATE NOT NULL,
  hora_inicio TIME NOT NULL,
  hora_fin TIME NOT NULL,
  estado TEXT NOT NULL DEFAULT 'programada' CHECK (estado IN ('programada', 'completada', 'cancelada_cliente', 'cancelada_centro', 'no_show')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_asistencias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  sesion_id UUID NOT NULL REFERENCES om_sesiones(id),
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  contrato_id UUID REFERENCES om_contratos(id),
  estado TEXT NOT NULL DEFAULT 'confirmada' CHECK (estado IN ('confirmada', 'asistio', 'no_vino', 'cancelada', 'recuperacion')),
  hora_cancelacion TIMESTAMPTZ,
  es_recuperacion BOOLEAN DEFAULT false,
  genera_cargo BOOLEAN DEFAULT false,
  cargo_monto NUMERIC(6,2),
  notas_instructor TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_cargos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  contrato_id UUID REFERENCES om_contratos(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('sesion_individual', 'cancelacion_tardia', 'suscripcion_grupo', 'producto', 'otro')),
  descripcion TEXT,
  base_imponible NUMERIC(8,2) NOT NULL,
  iva_porcentaje NUMERIC(4,2) NOT NULL DEFAULT 21.00,
  iva_monto NUMERIC(8,2) GENERATED ALWAYS AS (base_imponible * iva_porcentaje / 100) STORED,
  total NUMERIC(8,2) GENERATED ALWAYS AS (base_imponible * (1 + iva_porcentaje / 100)) STORED,
  sesion_id UUID REFERENCES om_sesiones(id),
  asistencia_id UUID REFERENCES om_asistencias(id),
  periodo_mes DATE,
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'cobrado', 'anulado')),
  fecha_cargo DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_cobro DATE,
  verifactu_hash TEXT,
  verifactu_enviado BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_pagos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  metodo TEXT NOT NULL CHECK (metodo IN ('tpv', 'bizum', 'efectivo', 'transferencia', 'paygold')),
  monto NUMERIC(8,2) NOT NULL,
  referencia_externa TEXT,
  fecha_pago DATE NOT NULL DEFAULT CURRENT_DATE,
  notas TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_pago_cargos (
  pago_id UUID NOT NULL REFERENCES om_pagos(id),
  cargo_id UUID NOT NULL REFERENCES om_cargos(id),
  monto_aplicado NUMERIC(8,2) NOT NULL,
  PRIMARY KEY (pago_id, cargo_id)
);

CREATE TABLE IF NOT EXISTS om_facturas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  numero_factura TEXT NOT NULL UNIQUE,
  serie TEXT NOT NULL DEFAULT 'AP',
  fecha_emision DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_operacion DATE,
  base_imponible NUMERIC(10,2) NOT NULL,
  iva_porcentaje NUMERIC(4,2) NOT NULL DEFAULT 21.00,
  iva_monto NUMERIC(10,2) NOT NULL,
  total NUMERIC(10,2) NOT NULL,
  estado TEXT NOT NULL DEFAULT 'emitida' CHECK (estado IN ('borrador', 'emitida', 'anulada', 'rectificativa')),
  verifactu_hash TEXT,
  verifactu_hash_anterior TEXT,
  verifactu_enviado BOOLEAN DEFAULT false,
  verifactu_timestamp TIMESTAMPTZ,
  verifactu_csv TEXT,
  cliente_nif TEXT,
  cliente_nombre_fiscal TEXT,
  cliente_direccion TEXT,
  pdf_path TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_factura_lineas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  factura_id UUID NOT NULL REFERENCES om_facturas(id),
  cargo_id UUID REFERENCES om_cargos(id),
  concepto TEXT NOT NULL,
  cantidad INT NOT NULL DEFAULT 1,
  precio_unitario NUMERIC(8,2) NOT NULL,
  base_imponible NUMERIC(8,2) NOT NULL,
  iva_porcentaje NUMERIC(4,2) NOT NULL DEFAULT 21.00,
  iva_monto NUMERIC(8,2) NOT NULL,
  total NUMERIC(8,2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_gastos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  categoria TEXT NOT NULL CHECK (categoria IN ('alquiler', 'seguros', 'suministros', 'material_pilates', 'limpieza', 'marketing', 'formacion', 'gestor', 'instructor', 'mantenimiento', 'software', 'otro')),
  descripcion TEXT NOT NULL,
  proveedor TEXT,
  base_imponible NUMERIC(10,2) NOT NULL,
  iva_porcentaje NUMERIC(4,2) DEFAULT 21.00,
  iva_soportado NUMERIC(10,2),
  total NUMERIC(10,2) NOT NULL,
  es_recurrente BOOLEAN DEFAULT false,
  periodicidad TEXT CHECK (periodicidad IN ('mensual', 'trimestral', 'anual')),
  fecha_gasto DATE NOT NULL,
  fecha_pago DATE,
  factura_recibida TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- BLOQUE 2: VOZ + CANALES (6 tablas)

CREATE TABLE IF NOT EXISTS om_voz_propuestas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  canal TEXT NOT NULL CHECK (canal IN ('whatsapp', 'google_business', 'instagram', 'facebook', 'email', 'web')),
  tipo TEXT NOT NULL CHECK (tipo IN ('broadcast', 'respuesta_resena', 'contenido', 'actualizacion_perfil', 'respuesta_dm', 'alerta_oportunidad', 'tarea_asistida')),
  eje1_irc NUMERIC(4,2),
  eje2_celda TEXT,
  eje3_formato TEXT,
  justificacion TEXT NOT NULL,
  contenido_propuesto JSONB NOT NULL,
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobada', 'ejecutada', 'descartada', 'editada')),
  fecha_propuesta TIMESTAMPTZ DEFAULT now(),
  fecha_decision TIMESTAMPTZ,
  fecha_ejecucion TIMESTAMPTZ,
  resultado JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_voz_telemetria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  canal TEXT NOT NULL,
  fecha DATE NOT NULL,
  leads_generados INT DEFAULT 0,
  reservas_directas INT DEFAULT 0,
  conversiones INT DEFAULT 0,
  mensajes_recibidos INT DEFAULT 0,
  mensajes_respondidos INT DEFAULT 0,
  tiempo_respuesta_medio_min INT,
  irc_calculado NUMERIC(4,2),
  pca_snapshot JSONB,
  metricas_raw JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(tenant_id, canal, fecha)
);

CREATE TABLE IF NOT EXISTS om_voz_isp (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  canal TEXT NOT NULL,
  fecha_auditoria DATE NOT NULL,
  isp_score NUMERIC(5,2) NOT NULL,
  elementos JSONB NOT NULL,
  acciones_generadas JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_voz_capa_a (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  fuente TEXT NOT NULL CHECK (fuente IN ('google_trends', 'meta_insights', 'gbp_api', 'ig_graph', 'wa_business', 'google_ads', 'ads_library', 'perplexity', 'outscraper', 'open_meteo', 'boe', 'ine', 'predicthq', 'sparktoro')),
  tipo_dato TEXT NOT NULL,
  datos JSONB NOT NULL,
  fecha_dato DATE NOT NULL,
  funcion_l07 TEXT,
  celda_matriz TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_mensajes_wa (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  direccion TEXT NOT NULL CHECK (direccion IN ('entrante', 'saliente')),
  remitente TEXT NOT NULL,
  destinatario TEXT NOT NULL,
  cliente_id UUID REFERENCES om_clientes(id),
  tipo_contenido TEXT NOT NULL CHECK (tipo_contenido IN ('texto', 'audio', 'imagen', 'video', 'documento', 'ubicacion', 'estado')),
  contenido TEXT,
  media_url TEXT,
  intencion TEXT CHECK (intencion IN ('consulta_precio', 'consulta_horario', 'reserva', 'cancelacion', 'feedback', 'queja', 'comando_dueno', 'nota_sesion', 'otro')),
  accion_generada TEXT,
  wa_message_id TEXT,
  wa_timestamp TIMESTAMPTZ,
  leido BOOLEAN DEFAULT false,
  respondido BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_llamadas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  cliente_id UUID REFERENCES om_clientes(id),
  telefono TEXT,
  direccion TEXT NOT NULL CHECK (direccion IN ('entrante', 'saliente', 'perdida')),
  fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
  duracion_seg INT,
  notas TEXT,
  intencion TEXT CHECK (intencion IN ('consulta', 'reserva', 'cancelacion', 'queja', 'seguimiento', 'otro')),
  requiere_callback BOOLEAN DEFAULT false,
  callback_completado BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- BLOQUE 3: L0_7 GAPS (5 tablas)

CREATE TABLE IF NOT EXISTS om_adn (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  categoria TEXT NOT NULL CHECK (categoria IN ('principio_innegociable', 'principio_flexible', 'metodo', 'filosofia', 'antipatron', 'criterio_depuracion')),
  titulo TEXT NOT NULL,
  descripcion TEXT NOT NULL,
  ejemplos JSONB,
  contra_ejemplos JSONB,
  funcion_l07 TEXT,
  lente TEXT,
  version INT DEFAULT 1,
  fecha_creacion DATE DEFAULT CURRENT_DATE,
  fecha_modificacion DATE,
  modificado_por TEXT,
  activo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_procesos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  area TEXT NOT NULL CHECK (area IN ('operativa_diaria', 'sesion', 'cliente', 'emergencia', 'administrativa', 'instructor')),
  titulo TEXT NOT NULL,
  descripcion TEXT NOT NULL,
  pasos JSONB NOT NULL,
  notas TEXT,
  funcion_l07 TEXT,
  vinculado_a_adn UUID REFERENCES om_adn(id),
  documentado_por TEXT,
  fecha_documentacion DATE DEFAULT CURRENT_DATE,
  ultima_revision DATE,
  version INT DEFAULT 1,
  veces_consultado INT DEFAULT 0,
  ultima_consulta TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_conocimiento (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('tecnica', 'cliente', 'negocio', 'mercado', 'metodo')),
  titulo TEXT NOT NULL,
  descripcion TEXT NOT NULL,
  evidencia JSONB,
  confianza TEXT CHECK (confianza IN ('hipotesis', 'validado', 'consolidado')),
  origen TEXT,
  sesion_id UUID REFERENCES om_sesiones(id),
  promovido_a_adn UUID REFERENCES om_adn(id),
  fecha_descubrimiento DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_onboarding_instructor (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  instructor_nombre TEXT NOT NULL,
  fecha_inicio DATE NOT NULL,
  evaluaciones JSONB NOT NULL DEFAULT '[]',
  estado TEXT DEFAULT 'en_curso' CHECK (estado IN ('en_curso', 'completado', 'fallido')),
  grado_absorcion NUMERIC(3,1),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_tensiones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('competencia_nueva', 'perdida_recurso', 'crisis_demanda', 'crecimiento', 'regulatorio', 'personal', 'estacional', 'mercado')),
  descripcion TEXT NOT NULL,
  funciones_afectadas TEXT[] NOT NULL,
  severidad TEXT NOT NULL CHECK (severidad IN ('baja', 'media', 'alta', 'critica')),
  fecha_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin DATE,
  duracion_estimada_dias INT,
  detectada_por TEXT NOT NULL,
  estado TEXT DEFAULT 'activa' CHECK (estado IN ('activa', 'resuelta', 'cronica')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- BLOQUE 4: SEQUITO + ACD (3 tablas)

CREATE TABLE IF NOT EXISTS om_sesiones_consejo (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  pregunta TEXT NOT NULL,
  contexto_adicional TEXT,
  profundidad TEXT DEFAULT 'normal' CHECK (profundidad IN ('rapida', 'normal', 'profunda')),
  tier_usado INT,
  estado_acd_pre TEXT,
  inteligencias_convocadas TEXT[] NOT NULL,
  pensamientos_seleccionados TEXT[],
  razonamientos_seleccionados TEXT[],
  prescripcion_acd JSONB,
  respuestas_por_asesor JSONB NOT NULL,
  sintesis TEXT NOT NULL,
  puntos_ciegos_cruzados TEXT[],
  decision_ternaria TEXT CHECK (decision_ternaria IN ('cierre', 'inerte', 'toxico')),
  decision_confianza NUMERIC(3,2),
  decision_razon TEXT,
  decision TEXT,
  decision_fecha DATE,
  accion_siguiente TEXT,
  coste_api NUMERIC(10,4),
  tiempo_ejecucion_s INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_diagnosticos_tenant (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  trigger TEXT NOT NULL CHECK (trigger IN ('briefing_semanal', 'sesion_consejo', 'manual', 'alerta_automatica', 'tension_detectada')),
  sesion_consejo_id UUID REFERENCES om_sesiones_consejo(id),
  vector_funcional JSONB NOT NULL,
  lentes JSONB NOT NULL,
  gradiente NUMERIC(4,3),
  gap NUMERIC(4,3),
  estado TEXT NOT NULL,
  estado_tipo TEXT NOT NULL CHECK (estado_tipo IN ('equilibrado', 'desequilibrado')),
  perfil_lentes TEXT,
  coalicion TEXT,
  atractor TEXT,
  flags TEXT[],
  repertorio JSONB,
  prescripcion JSONB,
  resultado TEXT CHECK (resultado IN ('cierre', 'inerte', 'toxico', 'pendiente')),
  metricas JSONB,
  coste_usd NUMERIC(10,4),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS om_depuracion (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('servicio_eliminar', 'cliente_toxico', 'gasto_innecesario', 'proceso_redundante', 'canal_inefectivo', 'habito_operativo', 'creencia_limitante')),
  descripcion TEXT NOT NULL,
  impacto_estimado TEXT,
  funcion_l07 TEXT,
  lente TEXT,
  origen TEXT NOT NULL CHECK (origen IN ('diagnostico_acd', 'sesion_consejo', 'manual', 'automatizacion')),
  diagnostico_id UUID REFERENCES om_diagnosticos_tenant(id),
  estado TEXT NOT NULL DEFAULT 'propuesta' CHECK (estado IN ('propuesta', 'aprobada', 'ejecutada', 'descartada')),
  fecha_propuesta DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_decision DATE,
  fecha_ejecucion DATE,
  resultado TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- BLOQUE 5: DIAS ESPERADOS

CREATE TABLE IF NOT EXISTS om_dias_esperados (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  contrato_id UUID NOT NULL REFERENCES om_contratos(id),
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  grupo_id UUID NOT NULL REFERENCES om_grupos(id),
  mes DATE NOT NULL,
  dias_esperados INT NOT NULL,
  dias_asistidos INT DEFAULT 0,
  dias_falta INT DEFAULT 0,
  dias_cancelados INT DEFAULT 0,
  dias_recuperados INT DEFAULT 0,
  pct_asistencia NUMERIC(5,2) GENERATED ALWAYS AS (
    CASE WHEN dias_esperados > 0
    THEN (dias_asistidos::numeric / dias_esperados * 100)
    ELSE 0 END
  ) STORED,
  recuperaciones_excedidas BOOLEAN GENERATED ALWAYS AS (
    dias_recuperados > dias_falta
  ) STORED,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(contrato_id, mes)
);

-- BLOQUE 6: BASE COMPARTIDA (2 tablas)

CREATE TABLE IF NOT EXISTS om_cliente_tenant (
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  tenant_id TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('lead', 'trial', 'activo', 'pausa', 'baja')),
  fecha_alta DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_baja DATE,
  motivo_baja TEXT,
  fuente_captacion TEXT,
  referido_por UUID REFERENCES om_clientes(id),
  derivado_desde TEXT,
  derivado_por TEXT,
  fecha_derivacion DATE,
  PRIMARY KEY (cliente_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS om_datos_clinicos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cliente_id UUID NOT NULL REFERENCES om_clientes(id),
  tenant_id TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('diagnostico', 'tratamiento_fisio', 'observacion_pilates', 'restriccion', 'medicacion', 'derivacion_medica', 'progreso', 'alta_clinica')),
  titulo TEXT NOT NULL,
  contenido TEXT NOT NULL,
  autor TEXT NOT NULL,
  visible_para TEXT[] NOT NULL DEFAULT '{}',
  fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_evento DATE,
  consentimiento_registrado BOOLEAN DEFAULT false,
  base_legal TEXT DEFAULT 'consentimiento',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- BLOQUE 7: ONBOARDING SELF-SERVICE

CREATE TABLE IF NOT EXISTS om_onboarding_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id TEXT NOT NULL,
  token TEXT NOT NULL UNIQUE,
  nombre_provisional TEXT,
  telefono TEXT,
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'completado', 'expirado')),
  cliente_id UUID REFERENCES om_clientes(id),
  fecha_creacion TIMESTAMPTZ DEFAULT now(),
  fecha_expiracion TIMESTAMPTZ,
  fecha_completado TIMESTAMPTZ,
  ip_completado TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- INDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_om_contratos_cliente ON om_contratos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_contratos_grupo ON om_contratos(grupo_id);
CREATE INDEX IF NOT EXISTS idx_om_contratos_tenant ON om_contratos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_sesiones_fecha ON om_sesiones(fecha);
CREATE INDEX IF NOT EXISTS idx_om_sesiones_grupo ON om_sesiones(grupo_id);
CREATE INDEX IF NOT EXISTS idx_om_sesiones_tenant_fecha ON om_sesiones(tenant_id, fecha);
CREATE INDEX IF NOT EXISTS idx_om_asistencias_sesion ON om_asistencias(sesion_id);
CREATE INDEX IF NOT EXISTS idx_om_asistencias_cliente ON om_asistencias(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_asistencias_tenant ON om_asistencias(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_cargos_cliente ON om_cargos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_cargos_estado ON om_cargos(estado);
CREATE INDEX IF NOT EXISTS idx_om_cargos_tenant ON om_cargos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_pagos_cliente ON om_pagos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_pagos_tenant ON om_pagos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_facturas_cliente ON om_facturas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_facturas_tenant ON om_facturas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_gastos_tenant ON om_gastos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_gastos_fecha ON om_gastos(fecha_gasto);
CREATE INDEX IF NOT EXISTS idx_om_mensajes_wa_cliente ON om_mensajes_wa(cliente_id);
CREATE INDEX IF NOT EXISTS idx_om_mensajes_wa_tenant ON om_mensajes_wa(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_diagnosticos_tenant_tid ON om_diagnosticos_tenant(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_diagnosticos_tenant_estado ON om_diagnosticos_tenant(estado);
CREATE INDEX IF NOT EXISTS idx_om_diagnosticos_tenant_created ON om_diagnosticos_tenant(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_om_datos_clinicos_cliente ON om_datos_clinicos(cliente_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_cliente_tenant_estado ON om_cliente_tenant(tenant_id, estado);
CREATE INDEX IF NOT EXISTS idx_om_depuracion_tenant ON om_depuracion(tenant_id);
CREATE INDEX IF NOT EXISTS idx_om_dias_esperados_contrato ON om_dias_esperados(contrato_id);
CREATE INDEX IF NOT EXISTS idx_om_dias_esperados_mes ON om_dias_esperados(mes);
CREATE INDEX IF NOT EXISTS idx_om_onboarding_links_token ON om_onboarding_links(token);
```

### 2. Deploy

```bash
cd @project/ && fly deploy --strategy immediate
```

### 3. Verificar tablas creadas

```bash
cd @project/ && python3 -c "
import asyncio, httpx

async def check():
    base = 'https://motor-semantico-omni.fly.dev'
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f'{base}/health')
        print(f'Health: {r.json()}')

asyncio.run(check())
"
```

Luego verificar logs:
```bash
fly logs -a motor-semantico-omni | grep -E 'migration_ok|om_pilates'
```

Y verificar tablas directamente:
```bash
fly postgres connect -a chief-os-omni -d chief_os_omni -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'om_%' ORDER BY tablename;"
```

**Pass/fail:**
- Deploy completa sin error
- Logs muestran `migration_ok` para `om_pilates_schema.sql`
- La query devuelve 29 tablas `om_*`
- `/health` responde OK

---

## NOTAS

- Todas las sentencias son `IF NOT EXISTS` — re-ejecutar no rompe nada
- Las tablas usan `gen_random_uuid()` de Postgres 13+ (fly.io tiene 15)
- `om_cargos` tiene columnas `GENERATED ALWAYS AS ... STORED` para IVA — Postgres 12+ las soporta
- `om_dias_esperados` tiene `GENERATED ALWAYS AS ... STORED` para pct_asistencia y recuperaciones_excedidas
- tenant_id = 'authentic_pilates' para todas las tablas con tenant
- om_clientes NO tiene tenant_id (es universal, compartido Pilates + Fisio)
- La relación cliente↔tenant vive en om_cliente_tenant (N:M)
