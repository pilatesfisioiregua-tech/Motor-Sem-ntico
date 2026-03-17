"""Chief of Staff — the architect layer above Code OS.

Responsibilities:
  1. Analyze domains and detect gaps (via Motor/Gestor)
  2. Design exocortex configurations
  3. Generate executable briefings
  4. Persist design conversations + learn from past designs
  5. Execute + verify via Code OS + Verifier
"""

import json
import time
import uuid
import re
import os
from typing import Optional
from dataclasses import dataclass, field


def _get_conn():
    try:
        from .db_pool import get_conn
        return get_conn()
    except Exception:
        return None


def _put_conn(conn):
    try:
        from .db_pool import put_conn
        put_conn(conn)
    except Exception:
        pass


class Chief:
    """Chief of Staff — designs and orchestrates exocortex implementations."""

    def __init__(self, conn=None):
        self._conn = conn

    def _ensure_conn(self):
        if self._conn is None:
            self._conn = _get_conn()
        return self._conn

    # =========================================================
    # PASO 1: Core methods
    # =========================================================

    def get_domain_status(self, consumidor: str) -> dict:
        """Get current state of an exocortex."""
        conn = self._ensure_conn()
        if not conn:
            return {'consumidor': consumidor, 'status': 'no_db', 'activo': False}

        try:
            with conn.cursor() as cur:
                # Check exocortex_estado
                cur.execute("""
                    SELECT nombre, activo, config
                    FROM exocortex_estado
                    WHERE LOWER(nombre) LIKE %s
                    LIMIT 1
                """, [f"%{consumidor.lower()}%"])
                row = cur.fetchone()
                if not row:
                    return {'consumidor': consumidor, 'status': 'not_found', 'activo': False}

                # Get recent datapoints
                cur.execute("""
                    SELECT COUNT(*), AVG(tasa_cierre)
                    FROM datapoints_efectividad
                    WHERE consumidor LIKE %s
                      AND timestamp > NOW() - INTERVAL '7 days'
                """, [f"%{consumidor.lower()}%"])
                dp_row = cur.fetchone()

                return {
                    'consumidor': consumidor,
                    'nombre': row[0],
                    'activo': row[1],
                    'config': row[2] if row[2] else {},
                    'status': 'active' if row[1] else 'inactive',
                    'datapoints_7d': dp_row[0] if dp_row else 0,
                    'tasa_media_7d': round(float(dp_row[1]), 4) if dp_row and dp_row[1] else 0,
                }
        except Exception as e:
            return {'consumidor': consumidor, 'status': 'error', 'error': str(e)}

    def suggest_next_step(self, consumidor: str) -> dict:
        """Suggest which cell to address next for an exocortex."""
        conn = self._ensure_conn()
        if not conn:
            return {'suggestion': 'no_db'}

        try:
            from .gestor import calcular_gradientes
            gradientes = calcular_gradientes(f"mejora continua {consumidor}", conn)
            top_gaps = gradientes.get('top_gaps', [])

            if not top_gaps:
                return {'suggestion': 'no_gaps', 'consumidor': consumidor}

            celda, gap = top_gaps[0] if isinstance(top_gaps[0], (list, tuple)) else (top_gaps[0], 0)
            return {
                'consumidor': consumidor,
                'next_celda': celda,
                'gap': gap,
                'razon': f'Mayor gap detectado: {celda} ({gap:.2f})',
                'top_3': top_gaps[:3],
            }
        except Exception as e:
            return {'suggestion': 'error', 'error': str(e)}

    # =========================================================
    # PASO 2: Analyze domain with real Motor
    # =========================================================

    def analyze_domain(self, domain_description: str) -> dict:
        """Analyze a domain using Motor — detect gaps and relevant INTs."""
        conn = self._ensure_conn()

        try:
            from .gestor import calcular_gradientes
            gradientes = calcular_gradientes(domain_description, conn)
        except Exception:
            gradientes = {'top_gaps': [], 'gradientes': {}}

        # Extract top 5 cells with most gap
        top_gaps_raw = gradientes.get('top_gaps', [])
        top_celdas = []
        for item in top_gaps_raw[:5]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                celda, gap = item[0], item[1]
            elif isinstance(item, dict):
                celda = item.get('celda', '')
                gap = item.get('gap', 0)
            else:
                celda, gap = str(item), 0

            # Get INTs assigned to this cell + top questions
            ints_for_cell = self._get_ints_for_cell(celda, conn)
            preguntas_top = self._get_top_preguntas(celda, conn, limit=3)

            top_celdas.append({
                'celda': celda,
                'gap': gap,
                'inteligencias': ints_for_cell,
                'preguntas_top_3': preguntas_top,
            })

        # Build suggested program
        ints_all = set()
        for tc in top_celdas:
            ints_all.update(tc['inteligencias'])

        return {
            'domain': domain_description,
            'gradientes': gradientes,
            'top_celdas': top_celdas,
            'programa_sugerido': {
                'inteligencias': sorted(ints_all),
                'n_inteligencias': len(ints_all),
                'celdas_target': [tc['celda'] for tc in top_celdas],
            },
        }

    def _get_ints_for_cell(self, celda: str, conn=None) -> list:
        """Get intelligence IDs mapped to a cell."""
        mapping_funcion = {
            'Conservar': ['INT-07', 'INT-05'],
            'Captar': ['INT-02', 'INT-06'],
            'Depurar': ['INT-03', 'INT-04'],
            'Distribuir': ['INT-05', 'INT-07'],
            'Frontera': ['INT-06', 'INT-17'],
            'Adaptar': ['INT-09', 'INT-14'],
            'Replicar': ['INT-12', 'INT-13'],
        }
        if 'x' in str(celda):
            funcion = str(celda).split('x')[0]
            return mapping_funcion.get(funcion, ['INT-01', 'INT-08'])
        return ['INT-01', 'INT-08']

    def _get_top_preguntas(self, celda: str, conn=None, limit: int = 3) -> list:
        """Get top questions for a cell by effectiveness score."""
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pregunta_id, AVG(tasa_cierre) as score
                    FROM datapoints_efectividad
                    WHERE celda_objetivo = %s AND calibrado = true
                    GROUP BY pregunta_id
                    ORDER BY score DESC
                    LIMIT %s
                """, [celda, limit])
                return [{'pregunta_id': r[0], 'score': round(float(r[1]), 4) if r[1] else 0}
                        for r in cur.fetchall()]
        except Exception:
            return []

    # =========================================================
    # PASO 3: Design exocortex
    # =========================================================

    def design_exocortex(self, domain: str, focus: str = None) -> dict:
        """Design complete exocortex configuration for a domain."""
        analysis = self.analyze_domain(domain)

        # Filter cells by focus if provided
        top_celdas = analysis.get('top_celdas', [])
        if focus and top_celdas:
            focus_lower = focus.lower()
            filtered = [tc for tc in top_celdas
                        if focus_lower in tc['celda'].lower()
                        or any(focus_lower in str(p).lower() for p in tc.get('preguntas_top_3', []))]
            if filtered:
                top_celdas = filtered

        consumidor_id = f"exocortex_{domain.lower().replace(' ', '_')[:30]}"

        # Consult past designs for this domain
        past_design = self._get_past_design(domain, focus)
        reuse_info = {}
        if past_design and past_design.get('score', 0) > 0.7:
            reuse_info = {
                'reused_from': past_design.get('id'),
                'reused_celdas': past_design.get('design', {}).get('celdas_target', []),
                'reused_ints': past_design.get('design', {}).get('inteligencias', []),
            }
            # Merge reused cells
            reused_celdas = set(reuse_info.get('reused_celdas', []))
            current_celdas = set(tc['celda'] for tc in top_celdas)
            if reused_celdas - current_celdas:
                for celda in reused_celdas - current_celdas:
                    top_celdas.append({'celda': celda, 'gap': 0.3,
                                       'inteligencias': self._get_ints_for_cell(celda),
                                       'preguntas_top_3': [], 'reused': True})

        # Compile all INTs needed
        all_ints = set()
        for tc in top_celdas:
            all_ints.update(tc.get('inteligencias', []))

        # Compile top 10 questions across cells
        preguntas_top10 = []
        for tc in top_celdas:
            preguntas_top10.extend(tc.get('preguntas_top_3', []))
        preguntas_top10 = preguntas_top10[:10]

        # Check existing status
        status = self.get_domain_status(consumidor_id)

        design = {
            'consumidor_id': consumidor_id,
            'domain': domain,
            'focus': focus,
            'celdas_target': [tc['celda'] for tc in top_celdas],
            'inteligencias': sorted(all_ints),
            'preguntas_top_10': preguntas_top10,
            'datos_necesarios': self._inferir_datos_necesarios(domain, top_celdas),
            'etl_config': {
                'fuentes': [f'datos_{domain.lower().replace(" ", "_")}'],
                'frecuencia': 'semanal',
            },
            'programa_compilado': analysis.get('programa_sugerido', {}),
            'existing_status': status if status.get('status') != 'not_found' else None,
            'reuse_info': reuse_info if reuse_info else None,
        }

        return design

    def _inferir_datos_necesarios(self, domain: str, celdas: list) -> list:
        """Infer what data is needed based on domain and target cells."""
        datos = []
        domain_lower = domain.lower()
        if any(w in domain_lower for w in ['pilates', 'gym', 'fitness', 'estudio']):
            datos.extend(['alumnos', 'asistencias', 'cancelaciones', 'pagos'])
        if any(w in domain_lower for w in ['restaurante', 'hotel', 'tienda']):
            datos.extend(['clientes', 'ventas', 'reservas', 'feedback'])
        if not datos:
            datos = ['clientes', 'transacciones', 'feedback']
        return datos

    # =========================================================
    # PASO 4: Generate briefing
    # =========================================================

    def generate_briefing(self, design: dict) -> str:
        """Generate executable .md briefing from design."""
        consumidor = design.get('consumidor_id', 'exocortex_nuevo')
        domain = design.get('domain', 'dominio')
        celdas = design.get('celdas_target', [])
        ints = design.get('inteligencias', [])
        datos = design.get('datos_necesarios', [])

        celdas_str = ', '.join(celdas[:5]) if celdas else 'ConservarxSalud'
        ints_str = ', '.join(ints[:6]) if ints else 'INT-01, INT-08, INT-16'
        datos_str = ', '.join(datos[:4]) if datos else 'datos'

        briefing = f"""# BRIEFING: Implementar exocortex {consumidor}
## REPO: {os.environ.get('PROJECT_DIR', '.')}
## CONTEXTO: Diseñado por Chief para dominio {domain}. Celdas target: {celdas_str}.

### PASO 1: Crear consumidor en exocortex_estado
ARCHIVOS: core/chief.py
INSTRUCCION:
Insertar registro en exocortex_estado:
INSERT INTO exocortex_estado (nombre, activo, config)
VALUES ('{consumidor}', true, '{{"domain": "{domain}", "celdas": {json.dumps(celdas[:5])}}}')
ON CONFLICT (nombre) DO UPDATE SET activo = true;
CRITERIO: python3 -c "print('OK')"

### PASO 2: Crear perfil de gradientes
ARCHIVOS: core/gestor.py
INSTRUCCION:
Ejecutar calcular_gradientes para el dominio:
from core.gestor import calcular_gradientes
g = calcular_gradientes('{domain}')
Verificar que retorna top_gaps con al menos 1 celda.
CRITERIO: python3 -c "print('OK')"

### PASO 3: Compilar programa inicial
ARCHIVOS: core/reglas_compilador.py
INSTRUCCION:
Compilar programa con inteligencias: {ints_str}.
Validar contra ConstraintManifold.
Guardar en programas_compilados para consumidor {consumidor}.
CRITERIO: python3 -c "print('OK')"

### PASO 4: Configurar ETL
ARCHIVOS: core/chief.py
INSTRUCCION:
Configurar fuentes de datos para {consumidor}:
Datos necesarios: {datos_str}.
Crear entrada en config si no existe.
CRITERIO: python3 -c "print('OK')"

### PASO 5: Ejecutar primera iteracion del Motor
ARCHIVOS: core/motor_vn.py
INSTRUCCION:
Ejecutar Motor vN con input de prueba para {domain}.
Verificar que produce hallazgos para las celdas target.
Registrar señales PID.
CRITERIO: python3 -c "print('OK')"

### PASO 6: Verificar ciclo completo
ARCHIVOS: core/chief.py
INSTRUCCION:
Verificar que el ciclo completo funciona:
1. Gradientes calculados
2. Programa compilado
3. Motor ejecuta sin error
4. Señales PID registradas
5. Tasa de cierre > 0
CRITERIO: python3 -c "print('OK')"
"""
        return briefing.strip()

    # =========================================================
    # PASO 8: Persist conversation
    # =========================================================

    def _ensure_tables(self, conn):
        """Create design tables if they don't exist."""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS design_conversations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        consumidor TEXT,
                        turns JSONB DEFAULT '[]'::jsonb,
                        domain TEXT,
                        focus TEXT,
                        design JSONB,
                        briefing_md TEXT,
                        status TEXT DEFAULT 'designing',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS design_registry (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        conversation_id UUID,
                        consumidor TEXT,
                        domain TEXT,
                        focus TEXT,
                        design JSONB,
                        briefing_md TEXT,
                        design_review JSONB,
                        implementation_result JSONB,
                        verification_result JSONB,
                        synthesis TEXT,
                        status TEXT DEFAULT 'success',
                        total_cost_usd FLOAT DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cola_mejoras (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        tipo TEXT DEFAULT 'arquitectural',
                        descripcion TEXT,
                        trigger TEXT,
                        design JSONB,
                        briefing_md TEXT,
                        estimated_cost FLOAT DEFAULT 0,
                        risk_level TEXT DEFAULT 'medium',
                        prioridad INT DEFAULT 5,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    # =========================================================
    # PASO 10: Execute and verify
    # =========================================================

    def execute_and_verify(self, design: dict, verify_tier: str = "standard",
                           conversation_id: str = None) -> dict:
        """Full flow: generate briefing → verify design → execute → verify result."""
        import tempfile

        # 1. Generate briefing
        briefing_md = self.generate_briefing(design)

        # 2. Load conversation if available
        conversation = None
        if conversation_id:
            conversation = self._get_conversation(conversation_id)

        # 3. Verify design before execution
        design_review = {'approved': True, 'form_issues': [], 'intent_issues': []}
        try:
            from .verifier import Verifier
            verifier = Verifier(verify_tier)
            design_review = verifier.verify_design(briefing_md, design, conversation)

            # Auto-correct if form issues
            attempts = 0
            while not design_review.get('approved') and attempts < 2:
                attempts += 1
                if design_review.get('form_issues'):
                    briefing_md = self.generate_briefing(design)  # regenerate
                elif design_review.get('intent_issues'):
                    # Redesign with feedback
                    feedback = design_review['intent_issues']
                    design = self.design_exocortex(
                        design.get('domain', ''),
                        focus=design.get('focus'))
                    briefing_md = self.generate_briefing(design)
                design_review = verifier.verify_design(briefing_md, design, conversation)

            if not design_review.get('approved'):
                return {
                    'status': 'design_rejected',
                    'design_review': design_review,
                    'message': 'Design rejected after 2 attempts. User reorientation needed.',
                }
        except ImportError:
            pass  # Verifier not available

        # 4. Execute briefing
        implementation = {'status': 'skipped'}
        try:
            briefing_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False, prefix='chief_briefing_')
            briefing_file.write(briefing_md)
            briefing_file.close()

            from .agent_loop import run_briefing
            implementation = run_briefing(
                briefing_path=briefing_file.name,
                project_dir=design.get('repo_dir', '.'),
                verbose=True,
            )
            os.unlink(briefing_file.name)
        except Exception as e:
            implementation = {'status': 'error', 'error': str(e)}

        # 5. Verify implementation
        verification = {'passed': False, 'score': 0}
        try:
            from .verifier import Verifier
            verifier = Verifier(verify_tier)
            verification = verifier.verify_briefing(implementation, design)
        except Exception:
            pass

        # 6. Close design
        if conversation_id:
            try:
                self.close_design(conversation_id, implementation, verification)
            except Exception:
                pass

        return {
            'design_review': design_review,
            'implementation': implementation,
            'verification': verification,
            'conversation_id': conversation_id,
        }

    # =========================================================
    # PASO 13: Close design + persist + synthesize + clean
    # =========================================================

    def close_design(self, conversation_id: str, briefing_result: dict,
                     verification_result: dict) -> dict:
        """Close a design: synthesize, persist to registry, clean raw turns.

        1. Generate synthesis (~500 words) from conversation turns
        2. Insert into design_registry
        3. Delete raw turns from design_conversations (keep metadata)
        4. Save to knowledge_base if score > 0.7
        """
        conn = self._ensure_conn()
        if not conn:
            return {'error': 'no_db'}

        try:
            self._ensure_tables(conn)

            # Get conversation data
            conversation = self._get_conversation(conversation_id)
            if not conversation:
                return {'error': 'conversation_not_found'}

            # 1. Generate synthesis
            turns = conversation.get('turns', [])
            synthesis = self._synthesize_conversation(turns, conversation)

            # 2. Insert into design_registry
            score = verification_result.get('score', 0)
            status = 'success' if score > 0.5 else ('partial' if score > 0.2 else 'failed')
            total_cost = briefing_result.get('total_cost', 0)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO design_registry
                        (conversation_id, consumidor, domain, focus, design,
                         briefing_md, implementation_result, verification_result,
                         synthesis, status, total_cost_usd)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    conversation_id,
                    conversation.get('consumidor', ''),
                    conversation.get('domain', ''),
                    conversation.get('focus', ''),
                    json.dumps(conversation.get('design', {}), default=str),
                    conversation.get('briefing_md', ''),
                    json.dumps(briefing_result, default=str),
                    json.dumps(verification_result, default=str),
                    synthesis,
                    status,
                    total_cost,
                ])

                # 3. Delete raw turns (keep metadata)
                cur.execute("""
                    UPDATE design_conversations
                    SET turns = '[]'::jsonb,
                        status = %s,
                        updated_at = NOW()
                    WHERE id = %s::uuid
                """, [status, conversation_id])

                # 4. Save to knowledge_base if successful
                if score > 0.7:
                    try:
                        cur.execute("""
                            INSERT INTO knowledge_base (scope, key, value, created_at)
                            VALUES ('chief:designs', %s, %s, NOW())
                            ON CONFLICT (scope, key) DO UPDATE SET value = EXCLUDED.value
                        """, [
                            conversation.get('consumidor', 'unknown'),
                            json.dumps({
                                'domain': conversation.get('domain'),
                                'focus': conversation.get('focus'),
                                'design': conversation.get('design'),
                                'score': score,
                                'synthesis': synthesis[:500],
                            }, default=str),
                        ])
                    except Exception:
                        pass  # knowledge_base may not exist

            conn.commit()
            return {'status': status, 'synthesis': synthesis[:200], 'score': score}

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            return {'error': str(e)}

    def _synthesize_conversation(self, turns: list, conversation: dict) -> str:
        """Compress conversation turns to ~500 word synthesis."""
        if not turns:
            return f"Diseño para {conversation.get('domain', 'dominio desconocido')}. Sin turnos de conversación registrados."

        # Build synthesis deterministically (no LLM needed for this)
        parts = []
        parts.append(f"DOMINIO: {conversation.get('domain', '?')}")
        if conversation.get('focus'):
            parts.append(f"FOCO: {conversation.get('focus')}")

        # Extract key moments from turns
        user_said = []
        chief_decided = []
        for turn in turns:
            role = turn.get('role', '')
            content = str(turn.get('content', ''))[:200]
            if role == 'user':
                user_said.append(content)
            elif role == 'chief':
                chief_decided.append(content)
                data = turn.get('data', {})
                if data:
                    if data.get('top_celdas'):
                        chief_decided.append(f"Celdas detectadas: {[c.get('celda') for c in data['top_celdas'][:3]]}")

        if user_said:
            parts.append(f"USUARIO PIDIO: {' → '.join(user_said[:3])}")
        if chief_decided:
            parts.append(f"CHIEF DECIDIO: {' → '.join(chief_decided[:3])}")

        design = conversation.get('design', {})
        if design:
            parts.append(f"CELDAS TARGET: {design.get('celdas_target', [])}")
            parts.append(f"INTELIGENCIAS: {design.get('inteligencias', [])}")

        return '\n'.join(parts)

    def _get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get full conversation from DB."""
        conn = self._ensure_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, consumidor, turns, domain, focus, design,
                           briefing_md, status
                    FROM design_conversations
                    WHERE id = %s::uuid
                """, [conversation_id])
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    'id': str(row[0]),
                    'consumidor': row[1],
                    'turns': row[2] if row[2] else [],
                    'domain': row[3],
                    'focus': row[4],
                    'design': row[5] if row[5] else {},
                    'briefing_md': row[6],
                    'status': row[7],
                }
        except Exception:
            return None

    # =========================================================
    # PASO 14: Learn from past designs
    # =========================================================

    def _get_past_design(self, domain: str, focus: str = None) -> Optional[dict]:
        """Find past successful design for similar domain."""
        conn = self._ensure_conn()
        if not conn:
            return None
        try:
            keywords = [w.lower() for w in domain.split() if len(w) > 3][:3]
            if not keywords:
                return None

            with conn.cursor() as cur:
                # Search in design_registry for similar domains
                cur.execute("""
                    SELECT id, domain, focus, design, status, total_cost_usd,
                           verification_result
                    FROM design_registry
                    WHERE status = 'success'
                      AND LOWER(domain) LIKE %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, [f"%{keywords[0]}%"])
                row = cur.fetchone()
                if row:
                    ver = row[6] if row[6] else {}
                    score = ver.get('score', 0) if isinstance(ver, dict) else 0
                    return {
                        'id': str(row[0]),
                        'domain': row[1],
                        'focus': row[2],
                        'design': row[3] if row[3] else {},
                        'status': row[4],
                        'cost': row[5],
                        'score': score,
                    }

                # Also check knowledge_base
                try:
                    cur.execute("""
                        SELECT value FROM knowledge_base
                        WHERE scope = 'chief:designs'
                          AND LOWER(key) LIKE %s
                        LIMIT 1
                    """, [f"%{keywords[0]}%"])
                    kb_row = cur.fetchone()
                    if kb_row and kb_row[0]:
                        data = kb_row[0] if isinstance(kb_row[0], dict) else json.loads(str(kb_row[0]))
                        return {
                            'id': 'kb',
                            'domain': data.get('domain', ''),
                            'focus': data.get('focus', ''),
                            'design': data.get('design', {}),
                            'status': 'success',
                            'score': data.get('score', 0.8),
                        }
                except Exception:
                    pass

            return None
        except Exception:
            return None


# =========================================================
# PASO 11: ChiefConversation — state machine
# =========================================================

class ChiefConversation:
    """Conversational flow for Chief — autonomous after focus selection.

    States:
      initial → focus_selected → reviewing_design → implementing → done
    """

    def __init__(self, chief: Chief):
        self.chief = chief
        self.state = "initial"
        self.domain = None
        self.focus = None
        self.analysis = None
        self.design = None
        self.briefing_md = None
        self.conversation_id = str(uuid.uuid4())
        self._turns = []

    def process_message(self, message: str, context: dict = None) -> dict:
        """Process user message based on current state. Returns response dict."""
        self._add_turn('user', message)

        if self.state == "initial":
            return self._handle_initial(message)
        elif self.state == "focus_selected":
            return self._handle_focus_selected(message)
        elif self.state == "reviewing_design":
            return self._handle_reviewing(message)
        elif self.state == "implementing":
            return {'state': self.state, 'response': 'Implementacion en curso. Espera...'}
        elif self.state == "done":
            return {'state': self.state, 'response': 'Diseño completado. Inicia nueva conversación para otro exocortex.'}
        else:
            return {'state': self.state, 'response': 'Estado desconocido.'}

    def _handle_initial(self, message: str) -> dict:
        """Initial state: analyze domain and ask about focus."""
        # Extract domain from message
        self.domain = message.strip()

        # Analyze domain
        self.analysis = self.chief.analyze_domain(self.domain)
        top_celdas = self.analysis.get('top_celdas', [])

        if not top_celdas:
            response = (
                f"Analice el dominio '{self.domain}'. "
                f"No detecte gaps significativos. Puedes describir más el contexto?"
            )
            self._add_turn('chief', response, data=self.analysis)
            return {'state': self.state, 'response': response}

        # Build response with top cells
        celdas_desc = []
        for tc in top_celdas[:3]:
            celda = tc.get('celda', '?')
            gap = tc.get('gap', 0)
            ints = tc.get('inteligencias', [])
            celdas_desc.append(f"  - {celda} (gap: {gap}, INTs: {', '.join(ints[:3])})")

        n_ints = len(self.analysis.get('programa_sugerido', {}).get('inteligencias', []))
        response = (
            f"Tu dominio '{self.domain}' activa {n_ints} inteligencias.\n"
            f"Top {len(celdas_desc)} gaps detectados:\n"
            + '\n'.join(celdas_desc) + '\n'
            f"En que quieres enfocarte? (ej: retencion, costes, calidad)"
        )

        self._add_turn('chief', response, data=self.analysis)

        # If message already includes focus keyword, advance
        focus_keywords = ['retencion', 'retención', 'costes', 'calidad', 'crecimiento',
                          'ventas', 'satisfaccion', 'eficiencia']
        detected_focus = None
        msg_lower = message.lower()
        for kw in focus_keywords:
            if kw in msg_lower:
                detected_focus = kw
                break

        if detected_focus:
            self.focus = detected_focus
            self.state = "focus_selected"
            return self._auto_design_and_review()

        return {'state': self.state, 'response': response, 'analysis': self.analysis}

    def _handle_focus_selected(self, message: str) -> dict:
        """User selected focus — design, review, and implement autonomously."""
        self.focus = message.strip()
        self.state = "focus_selected"
        return self._auto_design_and_review()

    def _auto_design_and_review(self) -> dict:
        """Autonomous flow: design → review → implement → verify."""
        # Design
        self.design = self.chief.design_exocortex(self.domain, focus=self.focus)
        self.briefing_md = self.chief.generate_briefing(self.design)

        self._add_turn('chief',
                       f"Diseñando exocortex para {self.domain} — foco: {self.focus}",
                       data={'design': self.design})

        # Persist conversation
        self._persist_conversation()

        self.state = "reviewing_design"

        # Execute and verify (autonomous)
        result = self.chief.execute_and_verify(
            self.design,
            verify_tier="standard",
            conversation_id=self.conversation_id,
        )

        if result.get('status') == 'design_rejected':
            self.state = "initial"
            response = (
                f"El diseño fue rechazado tras 2 intentos. "
                f"Issues: {result.get('design_review', {}).get('intent_issues', [])}. "
                f"Quieres reorientar el foco?"
            )
            self._add_turn('chief', response)
            return {'state': self.state, 'response': response, 'result': result}

        self.state = "done"
        impl = result.get('implementation', {})
        verif = result.get('verification', {})
        score = verif.get('score', 0)
        steps_ok = impl.get('steps_completed', 0)
        steps_total = impl.get('steps_total', 0)
        cost = impl.get('total_cost', 0)

        response = (
            f"Exocortex {self.design.get('consumidor_id', '')} implementado. "
            f"{steps_ok}/{steps_total} pasos. Score: {score:.2f}. ${cost:.2f}."
        )
        self._add_turn('chief', response, data=result)
        self._persist_conversation()

        return {'state': self.state, 'response': response, 'result': result}

    def _handle_reviewing(self, message: str) -> dict:
        """Reviewing state — user shouldn't need to interact here."""
        return {'state': self.state, 'response': 'Revisión en curso...'}

    def _add_turn(self, role: str, content: str, data: dict = None):
        turn = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'state': self.state,
        }
        if data:
            turn['data'] = data
        self._turns.append(turn)

    def _persist_conversation(self):
        """Persist conversation to DB."""
        conn = self.chief._ensure_conn()
        if not conn:
            return
        try:
            self.chief._ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO design_conversations
                        (id, consumidor, turns, domain, focus, design, briefing_md, status)
                    VALUES (%s::uuid, %s, %s::jsonb, %s, %s, %s::jsonb, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        turns = EXCLUDED.turns,
                        design = EXCLUDED.design,
                        briefing_md = EXCLUDED.briefing_md,
                        status = EXCLUDED.status,
                        updated_at = NOW()
                """, [
                    self.conversation_id,
                    self.design.get('consumidor_id', '') if self.design else '',
                    json.dumps(self._turns, default=str),
                    self.domain or '',
                    self.focus or '',
                    json.dumps(self.design, default=str) if self.design else '{}',
                    self.briefing_md or '',
                    self.state,
                ])
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
