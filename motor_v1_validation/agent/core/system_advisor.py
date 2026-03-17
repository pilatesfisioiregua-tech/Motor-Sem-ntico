"""System Advisor — Self-Driving CEO Intelligence.

Agrega senales de todos los subsistemas en acciones priorizadas para el CEO.
El sistema empuja al CEO a usar todo su potencial cognitivo.

Capacidades:
  1. Signal Aggregation: recolecta senales de 12+ subsistemas
  2. Action Ranking: prioriza acciones por impacto * urgencia
  3. Capability Discovery: detecta features dormidas
  4. Auto-Pilot: ejecuta acciones de bajo riesgo automaticamente
"""

import time
import json
from collections import defaultdict
from typing import Optional


# =====================================================
# CAPABILITY REGISTRY — all system capabilities
# =====================================================

SYSTEM_CAPABILITIES = {
    # --- Motor vN ---
    'motor_ejecutar': {
        'nombre': 'Motor vN — Ejecucion',
        'endpoint': 'POST /motor/ejecutar-vn',
        'descripcion': 'Ejecutar pipeline SFCE completo sobre un input en lenguaje natural',
        'categoria': 'ejecucion',
        'impacto': 10,
        'requisitos': ['OPENROUTER_API_KEY'],
    },
    'motor_sinema': {
        'nombre': 'Sinema — Inputs Ambiguos',
        'endpoint': 'POST /motor/ejecutar-sinema',
        'descripcion': 'Analizar inputs metaforicos/ambiguos con relajacion de restricciones',
        'categoria': 'ejecucion',
        'impacto': 7,
        'requisitos': ['OPENROUTER_API_KEY'],
    },
    # --- Gestor ---
    'gestor_loop': {
        'nombre': 'Gestor GAMC Loop',
        'endpoint': 'POST /gestor/loop',
        'descripcion': 'Ejecutar ciclo completo del Gestor: poda, promocion, recompilacion, auto-ajuste',
        'categoria': 'gestion',
        'impacto': 9,
        'requisitos': ['DATABASE_URL'],
    },
    'gestor_compilar': {
        'nombre': 'Compilar Programa',
        'endpoint': 'POST /gestor/compilar',
        'descripcion': 'Compilar programa de inteligencias optimizado para un input',
        'categoria': 'gestion',
        'impacto': 8,
        'requisitos': ['DATABASE_URL'],
    },
    'gestor_validar': {
        'nombre': 'Validar Programa',
        'endpoint': 'POST /gestor/validar-programa',
        'descripcion': 'Validar programa contra las 13 reglas del compilador (Constraint Manifold)',
        'categoria': 'gestion',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    'gestor_corregir': {
        'nombre': 'Corregir Programa',
        'endpoint': 'POST /gestor/corregir-programa',
        'descripcion': 'Proyectar programa invalido al punto mas cercano valido',
        'categoria': 'gestion',
        'impacto': 7,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Reactor ---
    'reactor_ejecutar': {
        'nombre': 'Reactor vN',
        'endpoint': 'POST /reactor/ejecutar',
        'descripcion': 'Generar preguntas candidatas desde gaps detectados',
        'categoria': 'evolucion',
        'impacto': 8,
        'requisitos': ['DATABASE_URL'],
    },
    'reactor_aprobar': {
        'nombre': 'Aprobar Candidatas',
        'endpoint': 'POST /reactor/aprobar/{id}',
        'descripcion': 'Promover preguntas candidatas del reactor a la Matriz',
        'categoria': 'evolucion',
        'impacto': 7,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Mejora Continua ---
    'mejora_detectar': {
        'nombre': 'Detectar Mejoras',
        'endpoint': 'POST /mejora/detectar',
        'descripcion': 'Escanear sistema en busca de oportunidades de mejora',
        'categoria': 'evolucion',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Nervous System ---
    'propiocepcion': {
        'nombre': 'Propiocepcion',
        'endpoint': 'GET /propiocepcion',
        'descripcion': 'Estado completo del sistema nervioso: salud, senales, metricas',
        'categoria': 'diagnostico',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
    'criticality': {
        'nombre': 'Motor Criticalidad',
        'endpoint': 'GET /criticality/estado',
        'descripcion': 'Temperatura, avalanchas, transiciones de fase — borde del caos',
        'categoria': 'diagnostico',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    'metacognitive': {
        'nombre': 'Metacognicion',
        'endpoint': 'POST /metacognitive/fok',
        'descripcion': 'Feeling of Knowing: estimar confianza antes de ejecutar',
        'categoria': 'diagnostico',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
    'predictive': {
        'nombre': 'Control Predictivo',
        'endpoint': 'GET /predictive/estado',
        'descripcion': 'MPC: predecir trayectorias + planificar acciones N ciclos ahead',
        'categoria': 'diagnostico',
        'impacto': 7,
        'requisitos': ['DATABASE_URL'],
    },
    'game_theory': {
        'nombre': 'Teoria de Juegos',
        'endpoint': 'GET /game-theory/estado',
        'descripcion': 'Nash equilibria, incentivos, Schelling points entre inteligencias',
        'categoria': 'diagnostico',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Monitoring ---
    'monitoring': {
        'nombre': 'Dashboard Monitoring',
        'endpoint': 'GET /monitoring/dashboard',
        'descripcion': 'Metricas 24h, SLOs, circuit breakers, presupuesto',
        'categoria': 'operaciones',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
    'test_suite': {
        'nombre': 'Test Suite Invariantes',
        'endpoint': 'POST /test-suite/run',
        'descripcion': 'Ejecutar 7 invariantes automatizados del sistema',
        'categoria': 'operaciones',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Exocortex ---
    'exocortex_ingest': {
        'nombre': 'Exocortex Ingestion',
        'endpoint': 'POST /exocortex/ingest',
        'descripcion': 'Ingestar datos externos para alimentar el sistema cognitivo',
        'categoria': 'datos',
        'impacto': 8,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Explorer ---
    'explorer': {
        'nombre': 'Pattern Explorer',
        'endpoint': 'POST /explorer/run',
        'descripcion': 'Explorar patrones cruzados entre scopes de conocimiento',
        'categoria': 'conocimiento',
        'impacto': 7,
        'requisitos': ['DATABASE_URL', 'OPENROUTER_API_KEY'],
    },
    'neural_search': {
        'nombre': 'Neural DB Search',
        'endpoint': 'POST /neural/search',
        'descripcion': 'Busqueda semantica con boost hebbiano en la base de conocimiento',
        'categoria': 'conocimiento',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Knowledge ---
    'info_redundancia': {
        'nombre': 'Analisis Redundancia',
        'endpoint': 'GET /info/redundancia',
        'descripcion': 'Detectar redundancia/complementariedad entre inteligencias',
        'categoria': 'conocimiento',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
    # --- Propagacion ---
    'propagacion': {
        'nombre': 'Propagacion de Cambios',
        'endpoint': 'POST /gestor/propagar',
        'descripcion': 'Propagar cambios en cascada entre tablas del sistema',
        'categoria': 'gestion',
        'impacto': 6,
        'requisitos': ['DATABASE_URL'],
    },
    'consistencia': {
        'nombre': 'Check Consistencia',
        'endpoint': 'GET /gestor/consistencia',
        'descripcion': 'Verificar consistencia cross-table del sistema',
        'categoria': 'operaciones',
        'impacto': 5,
        'requisitos': ['DATABASE_URL'],
    },
}


# =====================================================
# SYSTEM ADVISOR
# =====================================================

class SystemAdvisor:
    """Consejero del sistema — empuja al CEO a usar todo el potencial.

    Ciclo:
    1. Recolectar senales de todos los subsistemas
    2. Sintetizar en acciones priorizadas
    3. Presentar al CEO con contexto
    4. Ejecutar acciones aprobadas (o auto-ejecutar las de bajo riesgo)
    """

    def __init__(self):
        self.last_scan = 0
        self.cached_actions = []
        self.capability_usage = defaultdict(int)  # tracking
        self.auto_pilot = False

    def scan_system(self, conn=None) -> dict:
        """Escanear todos los subsistemas y generar acciones priorizadas."""
        own_conn = conn is None
        if own_conn:
            from .db_pool import get_conn
            conn = get_conn()
            if not conn:
                return self._scan_sin_db()

        try:
            actions = []

            # 1. Check autopoiesis
            actions.extend(self._check_autopoiesis(conn))

            # 2. Check PID signals
            actions.extend(self._check_pid_signals(conn))

            # 3. Check criticality
            actions.extend(self._check_criticality(conn))

            # 4. Check gestor health
            actions.extend(self._check_gestor(conn))

            # 5. Check reactor candidates
            actions.extend(self._check_reactor(conn))

            # 6. Check mejora queue
            actions.extend(self._check_mejoras(conn))

            # 7. Check dormant capabilities
            actions.extend(self._check_dormant_capabilities(conn))

            # 8. Check monitoring alerts
            actions.extend(self._check_senales(conn))

            # 9. Check data freshness
            actions.extend(self._check_data_freshness(conn))

            # 10. Check consistency
            actions.extend(self._check_consistency(conn))

            # Sort by priority (impacto * urgencia)
            actions.sort(key=lambda a: a.get('prioridad', 0), reverse=True)

            self.cached_actions = actions
            self.last_scan = time.time()

            return {
                'acciones': actions[:20],
                'n_total': len(actions),
                'timestamp': self.last_scan,
                'auto_pilot': self.auto_pilot,
                'subsistemas_escaneados': 10,
            }

        except Exception as e:
            return {'error': str(e), 'acciones': []}
        finally:
            if own_conn:
                from .db_pool import put_conn
                put_conn(conn)

    def _scan_sin_db(self) -> dict:
        """Scan basico sin conexion DB."""
        actions = [{
            'titulo': 'Verificar conexion a base de datos',
            'descripcion': 'No se puede conectar a la DB. Sin datos, el sistema cognitivo es ciego.',
            'categoria': 'critico',
            'prioridad': 100,
            'accion': 'GET /health',
            'auto_ejecutable': False,
            'icono': 'db',
        }]
        actions.extend(self._check_dormant_capabilities(None))
        actions.sort(key=lambda a: a.get('prioridad', 0), reverse=True)
        return {'acciones': actions[:20], 'n_total': len(actions), 'timestamp': time.time()}

    def _check_autopoiesis(self, conn) -> list:
        """Verificar ciclo autopoietico."""
        actions = []
        try:
            from .gestor_scheduler import get_scheduler
            scheduler = get_scheduler()
            auto = scheduler.check_autopoiesis()

            if auto.get('ciclo_roto'):
                broken = [k for k, v in auto.items()
                          if k.startswith('check_') and not v]
                actions.append({
                    'titulo': 'Ciclo autopoietico roto',
                    'descripcion': f'Checks fallidos: {", ".join(broken)}. El sistema no se auto-mantiene.',
                    'categoria': 'critico',
                    'prioridad': 95,
                    'accion': 'POST /gestor/loop',
                    'auto_ejecutable': True,
                    'icono': 'autopoiesis',
                })

            estado = scheduler.get_estado()
            if estado.get('ciclos_completados', 0) == 0:
                actions.append({
                    'titulo': 'Ejecutar primer ciclo del Gestor',
                    'descripcion': 'El Gestor nunca ha ejecutado su loop. Sin esto, la Matriz no aprende.',
                    'categoria': 'setup',
                    'prioridad': 90,
                    'accion': 'POST /gestor/loop',
                    'auto_ejecutable': True,
                    'icono': 'gestor',
                })
        except Exception:
            pass
        return actions

    def _check_pid_signals(self, conn) -> list:
        """Verificar senales PID de celdas."""
        actions = []
        try:
            with conn.cursor() as cur:
                # Celdas con I alto (gap cronico) y D >= 0 (no mejorando)
                cur.execute("""
                    SELECT celda_objetivo,
                           AVG(tasa_cierre) as tasa,
                           COUNT(*) as n
                    FROM datapoints_efectividad
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY celda_objetivo
                    HAVING AVG(tasa_cierre) < 0.15 AND COUNT(*) >= 5
                """)
                for row in cur.fetchall():
                    actions.append({
                        'titulo': f'Gap cronico: {row[0]}',
                        'descripcion': f'Tasa={round(float(row[1]), 3)} con {row[2]} intentos. Considerar poda/recompilacion.',
                        'categoria': 'optimizacion',
                        'prioridad': 70,
                        'accion': f'POST /gestor/loop',
                        'auto_ejecutable': True,
                        'icono': 'pid',
                    })
        except Exception:
            pass
        return actions

    def _check_criticality(self, conn) -> list:
        """Verificar temperatura del sistema."""
        actions = []
        try:
            from .criticality_engine import get_criticality_engine
            engine = get_criticality_engine()
            temp = engine.calcular_temperatura(conn)
            regimen = temp.get('regimen', '')

            if regimen == 'orden_rigido':
                actions.append({
                    'titulo': 'Sistema demasiado rigido',
                    'descripcion': f'T={temp.get("T")}, T_c={temp.get("T_c")}. Relajar restricciones para explorar mas.',
                    'categoria': 'ajuste',
                    'prioridad': 60,
                    'accion': 'POST /reactor/ejecutar',
                    'auto_ejecutable': True,
                    'icono': 'temp',
                })
            elif regimen == 'caos':
                actions.append({
                    'titulo': 'Sistema demasiado caotico',
                    'descripcion': f'T={temp.get("T")}. Endurecer restricciones del compilador.',
                    'categoria': 'ajuste',
                    'prioridad': 65,
                    'accion': 'POST /gestor/loop',
                    'auto_ejecutable': True,
                    'icono': 'temp',
                })
        except Exception:
            pass
        return actions

    def _check_gestor(self, conn) -> list:
        """Verificar salud del Gestor."""
        actions = []
        try:
            with conn.cursor() as cur:
                # Preguntas activas
                cur.execute("SELECT COUNT(*) FROM preguntas_matriz WHERE nivel NOT IN ('obsoleta', 'expirada')")
                n_preguntas = cur.fetchone()[0]

                if n_preguntas == 0:
                    actions.append({
                        'titulo': 'Matriz vacia — sin preguntas',
                        'descripcion': 'La Matriz no tiene preguntas activas. Ejecutar reactor para generar.',
                        'categoria': 'critico',
                        'prioridad': 95,
                        'accion': 'POST /reactor/ejecutar',
                        'auto_ejecutable': True,
                        'icono': 'matriz',
                    })

                # Programas compilados
                cur.execute("SELECT COUNT(*) FROM programas_compilados WHERE activo = true")
                n_programas = cur.fetchone()[0]

                if n_programas == 0:
                    actions.append({
                        'titulo': 'Sin programas compilados',
                        'descripcion': 'No hay programas compilados activos. El Motor no puede ejecutar sin ellos.',
                        'categoria': 'critico',
                        'prioridad': 90,
                        'accion': 'POST /gestor/loop',
                        'auto_ejecutable': True,
                        'icono': 'compilar',
                    })

                # Datapoints
                cur.execute("SELECT COUNT(*) FROM datapoints_efectividad")
                n_datapoints = cur.fetchone()[0]

                if n_datapoints < 10:
                    actions.append({
                        'titulo': f'Pocos datapoints ({n_datapoints})',
                        'descripcion': 'El sistema necesita mas ejecuciones para aprender. Ejecutar Motor vN con casos de prueba.',
                        'categoria': 'datos',
                        'prioridad': 75,
                        'accion': 'POST /motor/ejecutar-vn',
                        'auto_ejecutable': False,
                        'icono': 'datos',
                    })
        except Exception:
            pass
        return actions

    def _check_reactor(self, conn) -> list:
        """Verificar candidatas pendientes de reactor."""
        actions = []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM preguntas_matriz
                    WHERE nivel = 'candidata'
                """)
                n_candidatas = cur.fetchone()[0]

                if n_candidatas > 0:
                    actions.append({
                        'titulo': f'{n_candidatas} preguntas candidatas pendientes',
                        'descripcion': 'El Reactor genero preguntas que esperan aprobacion. Revisar y aprobar las validas.',
                        'categoria': 'revision',
                        'prioridad': 55,
                        'accion': 'GET /reactor/candidatas',
                        'auto_ejecutable': False,
                        'icono': 'reactor',
                    })
        except Exception:
            pass
        return actions

    def _check_mejoras(self, conn) -> list:
        """Verificar cola de mejoras."""
        actions = []
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM cola_mejoras WHERE estado = 'pendiente'")
                n = cur.fetchone()[0]
                if n > 0:
                    actions.append({
                        'titulo': f'{n} mejoras pendientes',
                        'descripcion': 'Hay mejoras detectadas esperando implementacion.',
                        'categoria': 'evolucion',
                        'prioridad': 45,
                        'accion': 'GET /mejora/cola',
                        'auto_ejecutable': False,
                        'icono': 'mejora',
                    })
        except Exception:
            pass
        return actions

    def _check_dormant_capabilities(self, conn) -> list:
        """Detectar capacidades dormidas — features no usadas."""
        actions = []
        used = set()

        if conn:
            try:
                with conn.cursor() as cur:
                    # Check recent activity per subsystem
                    cur.execute("SELECT COUNT(*) FROM datapoints_efectividad WHERE timestamp > NOW() - INTERVAL '7 days'")
                    if cur.fetchone()[0] > 0:
                        used.add('motor_ejecutar')

                    cur.execute("SELECT COUNT(*) FROM log_gestor WHERE created_at > NOW() - INTERVAL '7 days'")
                    if cur.fetchone()[0] > 0:
                        used.add('gestor_loop')

                    cur.execute("""
                        SELECT COUNT(*) FROM preguntas_matriz
                        WHERE nivel = 'candidata' AND created_at > NOW() - INTERVAL '7 days'
                    """)
                    if cur.fetchone()[0] > 0:
                        used.add('reactor_ejecutar')

                    cur.execute("SELECT COUNT(*) FROM marcas_estigmergicas WHERE created_at > NOW() - INTERVAL '7 days'")
                    if cur.fetchone()[0] > 0:
                        used.add('mejora_detectar')
            except Exception:
                pass

        # Find dormant capabilities
        dormant = []
        for cap_id, cap in SYSTEM_CAPABILITIES.items():
            if cap_id not in used and cap.get('impacto', 0) >= 7:
                dormant.append({
                    'id': cap_id,
                    **cap,
                })

        if dormant:
            dormant.sort(key=lambda c: c['impacto'], reverse=True)
            top = dormant[0]
            actions.append({
                'titulo': f'Capacidad dormida: {top["nombre"]}',
                'descripcion': f'{top["descripcion"]} (Impacto: {top["impacto"]}/10)',
                'categoria': 'descubrimiento',
                'prioridad': 50 + top['impacto'],
                'accion': top['endpoint'],
                'auto_ejecutable': False,
                'icono': 'unlock',
            })

            if len(dormant) > 1:
                actions.append({
                    'titulo': f'{len(dormant)} capacidades sin usar esta semana',
                    'descripcion': 'El sistema tiene potencial sin explotar. Revisa las capacidades disponibles.',
                    'categoria': 'descubrimiento',
                    'prioridad': 40,
                    'accion': 'GET /ceo/advisor/capabilities',
                    'auto_ejecutable': False,
                    'icono': 'discover',
                    'extra': {
                        'dormant_ids': [d['id'] for d in dormant[:10]],
                        'dormant_nombres': [d['nombre'] for d in dormant[:10]],
                    },
                })

        return actions

    def _check_senales(self, conn) -> list:
        """Verificar senales/alertas no resueltas."""
        actions = []
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM señales WHERE resuelta = false")
                n = cur.fetchone()[0]
                if n > 0:
                    cur.execute("""
                        SELECT tipo, severidad, mensaje FROM señales
                        WHERE resuelta = false
                        ORDER BY severidad DESC LIMIT 1
                    """)
                    top = cur.fetchone()
                    actions.append({
                        'titulo': f'{n} alerta(s) sin resolver',
                        'descripcion': f'Mas urgente: [{top[1]}] {top[2][:100]}' if top else '',
                        'categoria': 'alerta',
                        'prioridad': 80 if top and top[1] == 'critica' else 50,
                        'accion': 'GET /senales',
                        'auto_ejecutable': False,
                        'icono': 'alerta',
                    })
        except Exception:
            pass
        return actions

    def _check_data_freshness(self, conn) -> list:
        """Verificar frescura de los datos."""
        actions = []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(timestamp) FROM datapoints_efectividad
                """)
                row = cur.fetchone()
                if row and row[0]:
                    from datetime import datetime, timezone
                    last = row[0]
                    if hasattr(last, 'replace'):
                        now = datetime.now(timezone.utc)
                        if hasattr(last, 'tzinfo') and last.tzinfo is None:
                            last = last.replace(tzinfo=timezone.utc)
                        hours_ago = (now - last).total_seconds() / 3600
                        if hours_ago > 72:
                            actions.append({
                                'titulo': 'Datos obsoletos',
                                'descripcion': f'Ultimo datapoint hace {int(hours_ago)}h. El sistema necesita ejecuciones frescas.',
                                'categoria': 'datos',
                                'prioridad': 70,
                                'accion': 'POST /motor/ejecutar-vn',
                                'auto_ejecutable': False,
                                'icono': 'freshness',
                            })
                else:
                    actions.append({
                        'titulo': 'Sin datapoints',
                        'descripcion': 'El sistema nunca ha registrado una ejecucion. Ejecutar Motor vN para empezar a aprender.',
                        'categoria': 'setup',
                        'prioridad': 85,
                        'accion': 'POST /motor/ejecutar-vn',
                        'auto_ejecutable': False,
                        'icono': 'freshness',
                    })
        except Exception:
            pass
        return actions

    def _check_consistency(self, conn) -> list:
        """Verificar consistencia cross-table."""
        actions = []
        try:
            from .propagador import get_propagador
            prop = get_propagador()
            checks = prop.verificar_consistencia()
            inconsistencias = checks.get('inconsistencias', [])
            if inconsistencias:
                actions.append({
                    'titulo': f'{len(inconsistencias)} inconsistencia(s) detectada(s)',
                    'descripcion': inconsistencias[0].get('descripcion', '')[:100],
                    'categoria': 'integridad',
                    'prioridad': 55,
                    'accion': 'GET /gestor/consistencia',
                    'auto_ejecutable': False,
                    'icono': 'consistency',
                })
        except Exception:
            pass
        return actions

    def get_capabilities(self) -> dict:
        """Listar todas las capacidades del sistema con estado de uso."""
        caps = []
        for cap_id, cap in SYSTEM_CAPABILITIES.items():
            caps.append({
                'id': cap_id,
                **cap,
                'usos_recientes': self.capability_usage.get(cap_id, 0),
            })
        caps.sort(key=lambda c: c['impacto'], reverse=True)

        by_category = defaultdict(list)
        for c in caps:
            by_category[c['categoria']].append(c)

        return {
            'capacidades': caps,
            'n_total': len(caps),
            'por_categoria': dict(by_category),
            'categorias': list(by_category.keys()),
        }

    def execute_action(self, accion_endpoint: str) -> dict:
        """Ejecutar una accion recomendada.

        Para acciones seguras (GET, analisis), ejecuta directamente.
        Para acciones de escritura, retorna instrucciones.
        """
        self.capability_usage[accion_endpoint] = self.capability_usage.get(accion_endpoint, 0) + 1

        # Parse endpoint
        parts = accion_endpoint.split(' ', 1)
        method = parts[0] if len(parts) > 1 else 'GET'
        path = parts[1] if len(parts) > 1 else parts[0]

        # Auto-executable actions
        safe_actions = {
            'POST /gestor/loop': self._exec_gestor_loop,
            'POST /reactor/ejecutar': self._exec_reactor,
            'POST /mejora/detectar': self._exec_mejora_detectar,
            'POST /test-suite/run': self._exec_test_suite,
        }

        if accion_endpoint in safe_actions:
            try:
                result = safe_actions[accion_endpoint]()
                return {'status': 'ejecutado', 'resultado': result}
            except Exception as e:
                return {'status': 'error', 'error': str(e)}

        return {
            'status': 'requiere_input',
            'endpoint': accion_endpoint,
            'instrucciones': f'Ejecutar manualmente: {accion_endpoint}',
        }

    def _exec_gestor_loop(self) -> dict:
        from .gestor import get_gestor
        return get_gestor().ejecutar_loop()

    def _exec_reactor(self) -> dict:
        from .reactor_vn import get_reactor
        return get_reactor().ejecutar()

    def _exec_mejora_detectar(self) -> dict:
        from .mejora_continua import detectar_mejoras
        return {'mejoras': detectar_mejoras()}

    def _exec_test_suite(self) -> dict:
        from tests.test_invariants import run_all_invariants
        return run_all_invariants()


# Singleton
_advisor = None

def get_advisor() -> SystemAdvisor:
    global _advisor
    if _advisor is None:
        _advisor = SystemAdvisor()
    return _advisor
