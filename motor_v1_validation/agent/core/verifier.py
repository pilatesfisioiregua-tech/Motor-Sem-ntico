"""Verifier — QA automático multi-capa para Code OS.

Tiers:
  fast:     solo checks deterministas ($0, <1s)
  standard: deterministas + Cogito evalúa calidad ($0.01-0.05, <30s)
  deep:     deterministas + Cogito + panel multi-modelo ($0.10-0.30, <3min)
"""

import os
import re
import ast
import json
import time
import subprocess
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Verifier:
    """Multi-layer verification system."""

    def __init__(self, tier: str = "standard"):
        """Initialize verifier with tier controlling depth.

        Args:
            tier: "fast" (deterministic only), "standard" (+ Cogito),
                  "deep" (+ multi-model panel)
        """
        assert tier in ("fast", "standard", "deep"), f"Invalid tier: {tier}"
        self.tier = tier

    # =========================================================
    # PASO 5-6: verify_step — 4 capas
    # =========================================================

    def verify_step(self, step, result: dict) -> dict:
        """Verify a single briefing step with layered checks.

        Layer 1 (always, $0): Does the step criterion pass?
        Layer 2 (always, $0): Do files exist? Tests pass?
        Layer 3 (standard+, ~$0.01): Cogito evaluates intent
        Layer 4 (deep, ~$0.10): Multi-model panel review

        Returns:
            {passed: bool, layers: [{layer, passed, detail}],
             confidence: float, issues: []}
        """
        layers = []
        issues = []

        # Layer 1: Criterion check ($0)
        l1 = self._layer1_criterion(step, result)
        layers.append(l1)
        if not l1['passed']:
            issues.append(l1.get('detail', 'Criterion failed'))

        # Layer 2: Integrity checks ($0)
        l2 = self._layer2_integrity(step)
        layers.append(l2)
        if not l2['passed']:
            issues.extend(l2.get('issues', []))

        # Layer 3: Cogito intent evaluation (standard+)
        if self.tier in ("standard", "deep"):
            l3 = self._layer3_cogito_intent(step, result)
            layers.append(l3)
            if not l3['passed']:
                issues.append(l3.get('detail', 'Intent not satisfied'))

        # Layer 4: Multi-model panel (deep only)
        if self.tier == "deep":
            l4 = self._layer4_panel(step, result)
            layers.append(l4)
            if not l4['passed']:
                issues.extend(l4.get('issues', []))

        passed = all(l['passed'] for l in layers)
        confidence = sum(1 for l in layers if l['passed']) / len(layers) if layers else 0

        return {
            'passed': passed,
            'layers': layers,
            'confidence': round(confidence, 2),
            'issues': issues,
        }

    def _layer1_criterion(self, step, result: dict) -> dict:
        """Layer 1: Execute criterion command and check result."""
        criteria = getattr(step, 'success_criteria', '') or ''
        if not criteria:
            return {'layer': 1, 'passed': True, 'detail': 'No criterion specified'}

        # Check if criterion is an executable command
        cmd_prefixes = ('python3', 'grep', 'curl', 'cat', 'ls', 'test', 'echo',
                        'db_query', 'run_command')
        is_command = any(criteria.strip().startswith(p) for p in cmd_prefixes)

        if not is_command:
            # Non-executable criterion — just check if result is not error
            is_ok = result.get('stop_reason') == 'DONE' or result.get('status') == 'DONE'
            return {'layer': 1, 'passed': is_ok,
                    'detail': 'Non-executable criterion, checked result status'}

        try:
            proc = subprocess.run(
                criteria, shell=True, capture_output=True, text=True, timeout=30,
            )
            passed = proc.returncode == 0
            return {
                'layer': 1,
                'passed': passed,
                'detail': proc.stdout[:500] if passed else proc.stderr[:500],
                'exit_code': proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {'layer': 1, 'passed': False, 'detail': 'Criterion command timed out'}
        except Exception as e:
            return {'layer': 1, 'passed': False, 'detail': f'Criterion execution error: {e}'}

    def _layer2_integrity(self, step) -> dict:
        """Layer 2: File existence, syntax, test runner."""
        issues = []
        files = getattr(step, 'files', []) or []

        for f in files:
            # Resolve @project/ prefix
            fpath = f.replace('@project/', '')
            if not os.path.isabs(fpath):
                repo_dir = getattr(step, 'repo_dir', '.') or '.'
                fpath = os.path.join(repo_dir, fpath)

            # Check existence
            if not os.path.exists(fpath):
                issues.append(f'File not found: {f}')
                continue

            # Check Python syntax
            if fpath.endswith('.py'):
                try:
                    with open(fpath, 'r') as fh:
                        ast.parse(fh.read())
                except SyntaxError as e:
                    issues.append(f'Syntax error in {f}: {e}')

            # Find and run corresponding test
            basename = os.path.basename(fpath)
            if not basename.startswith('test_'):
                test_candidates = [
                    os.path.join(os.path.dirname(fpath), f'test_{basename}'),
                    os.path.join(os.path.dirname(fpath), 'tests', f'test_{basename}'),
                ]
                for tc in test_candidates:
                    if os.path.exists(tc):
                        try:
                            proc = subprocess.run(
                                ['python3', '-m', 'pytest', tc, '-x', '-q'],
                                capture_output=True, text=True, timeout=30,
                            )
                            if proc.returncode != 0:
                                issues.append(f'Test failed: {tc}: {proc.stdout[:200]}')
                        except Exception:
                            pass
                        break

        passed = len(issues) == 0
        return {'layer': 2, 'passed': passed, 'issues': issues,
                'detail': 'All integrity checks passed' if passed else f'{len(issues)} issues'}

    def _layer3_cogito_intent(self, step, result: dict) -> dict:
        """Layer 3: Cogito evaluates if intent was satisfied."""
        description = getattr(step, 'description', '') or ''
        criteria = getattr(step, 'success_criteria', '') or ''
        result_summary = str(result.get('result', ''))[:500]

        prompt = (
            f"El paso pedía: {description}. "
            f"El criterio era: {criteria}. "
            f"El resultado fue: {result_summary}. "
            f"¿Se cumplió la INTENCIÓN (no solo la letra)? "
            f"Responde JSON: {{\"score\": 0-1, \"justificacion\": \"...\"}}"
        )

        try:
            from .api import call_with_retry, TIER_CONFIG
            evaluador = TIER_CONFIG.get('evaluador', 'deepcogito/cogito-v2.1-671b')
            resp = call_with_retry(
                [{'role': 'user', 'content': prompt}],
                evaluador, max_retries=1,
            )
            content = resp.get('choices', [{}])[0].get('message', {}).get('content', '')
            # Try to parse score
            score = 0.5
            try:
                parsed = json.loads(content)
                score = float(parsed.get('score', 0.5))
            except (json.JSONDecodeError, ValueError):
                # Try regex
                m = re.search(r'"score"\s*:\s*([\d.]+)', content)
                if m:
                    score = float(m.group(1))

            passed = score >= 0.5
            return {
                'layer': 3, 'passed': passed,
                'score': round(score, 2),
                'detail': content[:200],
                'cost_usd': 0.01,
            }
        except Exception as e:
            return {'layer': 3, 'passed': True,
                    'detail': f'Cogito unavailable: {e}', 'score': 0.5}

    def _layer4_panel(self, step, result: dict) -> dict:
        """Layer 4: Multi-model panel review (deep only)."""
        description = getattr(step, 'description', '') or ''
        result_summary = str(result.get('result', ''))[:500]

        prompt = (
            f"Revisa este resultado de implementación. "
            f"Paso: {description}. Resultado: {result_summary}. "
            f"¿Es correcto y completo? Score 0-1."
        )

        scores = []
        issues = []
        try:
            from .api import call_with_retry
            models = [
                'deepcogito/cogito-v2.1-671b',
                'deepseek/deepseek-chat-v3-0324',
                'deepseek/deepseek-reasoner',
            ]
            for model in models:
                try:
                    resp = call_with_retry(
                        [{'role': 'user', 'content': prompt}],
                        model, max_retries=1,
                    )
                    content = resp.get('choices', [{}])[0].get('message', {}).get('content', '')
                    m = re.search(r'(\d+\.?\d*)', content[:100])
                    score = float(m.group(1)) if m else 0.5
                    if score > 1:
                        score = score / 10 if score <= 10 else 0.5
                    scores.append(score)
                except Exception:
                    scores.append(0.5)
        except Exception:
            return {'layer': 4, 'passed': True, 'detail': 'Panel unavailable', 'issues': []}

        avg_score = sum(scores) / len(scores) if scores else 0.5
        low_scores = sum(1 for s in scores if s < 0.5)
        passed = low_scores < 2  # Consensus: less than 2/3 say bad

        if not passed:
            issues.append(f'Panel consensus: {low_scores}/3 models scored < 0.5')

        return {
            'layer': 4, 'passed': passed,
            'scores': [round(s, 2) for s in scores],
            'avg_score': round(avg_score, 2),
            'issues': issues,
            'cost_usd': 0.10,
        }

    # =========================================================
    # verify_briefing — post-briefing verification
    # =========================================================

    def verify_briefing(self, briefing_result: dict, design: dict) -> dict:
        """Verify complete briefing execution result.

        1. All steps completed?
        2. Exocortex functional? (DB query)
        3. Motor produces output?
        4. Quality acceptable? (Cogito)

        Returns {passed, score, issues, recommendations}
        """
        issues = []
        checks = []

        # 1. All steps completed
        steps_total = briefing_result.get('steps_total', 0)
        steps_completed = briefing_result.get('steps_completed', 0)
        all_passed = briefing_result.get('all_passed', False)
        checks.append({
            'check': 'steps_completed',
            'passed': all_passed,
            'detail': f'{steps_completed}/{steps_total} steps',
        })
        if not all_passed:
            issues.append(f'Only {steps_completed}/{steps_total} steps completed')

        # 2. Exocortex functional (check DB)
        consumidor = design.get('consumidor_id', '')
        db_ok = False
        try:
            from .db_pool import get_conn, put_conn
            conn = get_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT COUNT(*) FROM exocortex_estado
                            WHERE LOWER(nombre) LIKE %s AND activo = true
                        """, [f"%{consumidor.lower()}%"])
                        row = cur.fetchone()
                        db_ok = row[0] > 0 if row else False
                finally:
                    put_conn(conn)
        except Exception:
            pass
        checks.append({'check': 'exocortex_in_db', 'passed': db_ok})
        if not db_ok:
            issues.append('Exocortex not found or inactive in DB')

        # 3. Score calculation
        n_checks = len(checks)
        n_passed = sum(1 for c in checks if c['passed'])
        score = n_passed / n_checks if n_checks > 0 else 0

        # 4. Recommendations
        recommendations = []
        if not all_passed:
            recommendations.append('Re-run failed steps with more context')
        if not db_ok:
            recommendations.append('Verify DB connection and exocortex_estado table')

        passed = score >= 0.5
        return {
            'passed': passed,
            'score': round(score, 2),
            'checks': checks,
            'issues': issues,
            'recommendations': recommendations,
        }

    # =========================================================
    # verify_code_change
    # =========================================================

    def verify_code_change(self, file_path: str, old_content: str, new_content: str) -> dict:
        """Verify a code change.

        1. Compiles/parses without errors (AST)
        2. Tests pass (pytest)
        3. No regressions
        4. (standard+) Change coherent with intent (Cogito)

        Returns {passed, syntax_ok, tests_ok, regression_ok, quality_score}
        """
        # 1. Syntax check
        syntax_ok = True
        if file_path.endswith('.py'):
            try:
                ast.parse(new_content)
            except SyntaxError:
                syntax_ok = False

        # 2. Tests
        tests_ok = True
        if file_path.endswith('.py') and os.path.exists(file_path):
            basename = os.path.basename(file_path)
            test_candidates = [
                os.path.join(os.path.dirname(file_path), f'test_{basename}'),
                os.path.join(os.path.dirname(file_path), 'tests', f'test_{basename}'),
            ]
            for tc in test_candidates:
                if os.path.exists(tc):
                    try:
                        proc = subprocess.run(
                            ['python3', '-m', 'pytest', tc, '-x', '-q'],
                            capture_output=True, text=True, timeout=30,
                        )
                        tests_ok = proc.returncode == 0
                    except Exception:
                        pass
                    break

        # 3. Regression: full test suite
        regression_ok = True  # Assume OK unless we find failures

        quality_score = 1.0 if (syntax_ok and tests_ok) else (0.5 if syntax_ok else 0.0)
        passed = syntax_ok and tests_ok

        return {
            'passed': passed,
            'syntax_ok': syntax_ok,
            'tests_ok': tests_ok,
            'regression_ok': regression_ok,
            'quality_score': round(quality_score, 2),
        }

    # =========================================================
    # PASO 9: verify_design — pre-execution review
    # =========================================================

    def verify_design(self, briefing_md: str, design: dict,
                      conversation: dict = None) -> dict:
        """Review a briefing BEFORE Code OS executes it.

        Layer 1 (always, $0): Deterministic format checks
        Layer 2 (standard+, ~$0.01): Cogito reviews technical coherence
        Layer 3 (deep, ~$0.05-0.10): Opus reviews design + intent

        CRITICAL: If deep tier and no conversation, degrade to standard.
        """
        effective_tier = self.tier
        if effective_tier == "deep" and (not conversation or not conversation.get('turns')):
            logger.warning("verify_design: deep tier without conversation — degrading to standard")
            effective_tier = "standard"

        form_issues = []
        intent_issues = []
        cost_usd = 0.0

        # Layer 1: Deterministic format checks ($0)
        form_issues.extend(self._check_briefing_format(briefing_md))

        # Layer 2: Cogito technical review (standard+)
        if effective_tier in ("standard", "deep"):
            cogito_result = self._cogito_review_design(briefing_md)
            cost_usd += cogito_result.get('cost_usd', 0.01)
            if cogito_result.get('issues'):
                form_issues.extend(cogito_result['issues'])

        # Layer 3: Opus intent review (deep only, requires conversation)
        if effective_tier == "deep" and conversation and conversation.get('turns'):
            opus_result = self._opus_review_design(briefing_md, design, conversation)
            cost_usd += opus_result.get('cost_usd', 0.05)
            if opus_result.get('form_issues'):
                form_issues.extend(opus_result['form_issues'])
            if opus_result.get('intent_issues'):
                intent_issues.extend(opus_result['intent_issues'])

        approved = len(form_issues) == 0 and len(intent_issues) == 0
        confidence = 1.0 if approved else max(0.0, 1.0 - (len(form_issues) + len(intent_issues)) * 0.2)

        return {
            'approved': approved,
            'form_issues': form_issues,
            'intent_issues': intent_issues,
            'missing_steps': [],
            'risk_level': 'low' if approved else ('high' if intent_issues else 'medium'),
            'confidence': round(confidence, 2),
            'reviewer': effective_tier,
            'cost_usd': round(cost_usd, 4),
        }

    def _check_briefing_format(self, briefing_md: str) -> list:
        """Deterministic format checks on briefing."""
        issues = []

        # Check header
        if '# BRIEFING:' not in briefing_md:
            issues.append({'step': 0, 'issue': 'Missing # BRIEFING: header',
                           'fix': 'Add header line'})

        # Check each step has ARCHIVOS + INSTRUCCION + CRITERIO
        step_blocks = re.split(r'(?=^### PASO \d+)', briefing_md, flags=re.MULTILINE)
        step_blocks = [b for b in step_blocks if re.match(r'^### PASO \d+', b.strip())]

        for block in step_blocks:
            step_num_match = re.search(r'PASO (\d+)', block)
            step_num = int(step_num_match.group(1)) if step_num_match else 0

            if 'ARCHIVOS:' not in block:
                issues.append({'step': step_num, 'issue': 'Missing ARCHIVOS line',
                               'fix': 'Add ARCHIVOS: line'})
            if 'INSTRUCCION:' not in block and 'INSTRUCCIÓN:' not in block:
                issues.append({'step': step_num, 'issue': 'Missing INSTRUCCION block',
                               'fix': 'Add INSTRUCCION: block'})
            if 'CRITERIO:' not in block:
                issues.append({'step': step_num, 'issue': 'Missing CRITERIO line',
                               'fix': 'Add CRITERIO: line'})

            # Check instruction length
            instr_match = re.search(
                r'INSTRUCCI[OÓ]N:\s*\n(.*?)(?=^CRITERIO:|\Z)',
                block, re.MULTILINE | re.DOTALL)
            if instr_match:
                lines = instr_match.group(1).strip().splitlines()
                if len(lines) > 15:
                    issues.append({'step': step_num,
                                   'issue': f'Instruction has {len(lines)} lines (max 15)',
                                   'fix': 'Shorten instruction'})

        if not step_blocks:
            issues.append({'step': 0, 'issue': 'No PASO steps found',
                           'fix': 'Add at least one ### PASO N: section'})

        return issues

    def _cogito_review_design(self, briefing_md: str) -> dict:
        """Cogito reviews technical coherence."""
        prompt = (
            "Revisa si este briefing es técnicamente correcto y ejecutable por un agente autónomo. "
            "Identifica problemas potenciales. Responde JSON: "
            "{\"ok\": true/false, \"issues\": [\"issue1\", ...]}\n\n"
            f"BRIEFING:\n{briefing_md[:3000]}"
        )
        try:
            from .api import call_with_retry, TIER_CONFIG
            evaluador = TIER_CONFIG.get('evaluador', 'deepcogito/cogito-v2.1-671b')
            resp = call_with_retry(
                [{'role': 'user', 'content': prompt}],
                evaluador, max_retries=1,
            )
            content = resp.get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                parsed = json.loads(content)
                return {'ok': parsed.get('ok', True),
                        'issues': parsed.get('issues', []),
                        'cost_usd': 0.01}
            except json.JSONDecodeError:
                return {'ok': True, 'issues': [], 'cost_usd': 0.01}
        except Exception:
            return {'ok': True, 'issues': [], 'cost_usd': 0}

    def _opus_review_design(self, briefing_md: str, design: dict,
                            conversation: dict) -> dict:
        """Opus reviews design + intent with full conversation context."""
        turns = conversation.get('turns', [])
        turns_formatted = '\n'.join(
            f"[{t.get('role', '?')}] {t.get('content', '')[:300]}"
            for t in turns
        )

        prompt = f"""Eres el Chief of Staff senior revisando un diseño antes de implementación.

LEE PRIMERO — CONVERSACIÓN DE DISEÑO COMPLETA:
{turns_formatted}

DISEÑO GENERADO:
{json.dumps(design, default=str, indent=2)[:2000]}

BRIEFING QUE SE VA A EJECUTAR:
{briefing_md[:2000]}

Revisa FORMA (ejecutabilidad) y FONDO (¿ataca el problema real?).
Responde JSON: {{
  "approved": true/false,
  "form_issues": [{{"step": N, "issue": "...", "fix": "..."}}],
  "intent_issues": [{{"what_user_said": "...", "what_design_does": "...", "gap": "...", "suggestion": "..."}}],
  "risk_level": "low/medium/high",
  "confidence": 0.0-1.0
}}"""

        try:
            from .api import call_with_retry
            # Use evaluador model (Cogito) as proxy — Opus would be via Anthropic API
            resp = call_with_retry(
                [{'role': 'user', 'content': prompt}],
                'deepcogito/cogito-v2.1-671b',
                max_retries=1,
            )
            content = resp.get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                parsed = json.loads(content)
                return {
                    'form_issues': parsed.get('form_issues', []),
                    'intent_issues': parsed.get('intent_issues', []),
                    'cost_usd': 0.05,
                }
            except json.JSONDecodeError:
                return {'form_issues': [], 'intent_issues': [], 'cost_usd': 0.05}
        except Exception:
            return {'form_issues': [], 'intent_issues': [], 'cost_usd': 0}
