"""Tests de integracion Sprints 4-6 Matrioska.

Verifica que los 5 niveles importan y se conectan correctamente.
Tests offline (no requieren DB ni LLM).
"""
import asyncio
import sys
import os

# Asegurar que motor-semantico/ esta en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ============================================================
# SPRINT 0-3: Verificar que todo sigue importando
# ============================================================

class TestImportsBasicos:
    """Los 5 niveles Matrioska importan sin errores."""

    def test_kernel_imports(self):
        from kernel.verificador import verificar
        assert callable(verificar)

    def test_motor_imports(self):
        from motor.pensar import pensar, ConfigPensamiento, Pensamiento
        assert callable(pensar)
        c = ConfigPensamiento(funcion="F3", complejidad="media")
        assert c.funcion == "F3"

    def test_organismo_nodo_vivo(self):
        from organismo.nodo_vivo import NodoVivo, Senal, TIPOS_SENAL
        assert len(TIPOS_SENAL) == 6
        s = Senal(origen="test", tipo="ALERTA", payload={"test": True})
        assert s.prioridad == 5

    def test_organismo_pizarra(self):
        from organismo.pizarras.pizarra import PizarraUnificada, TIPOS_PIZARRA
        assert len(TIPOS_PIZARRA) == 8
        p = PizarraUnificada("test_tenant")
        assert p.tenant_id == "test_tenant"

    def test_organismo_agente_funcional(self):
        from organismo.agentes.agente_funcional import AgenteFuncional
        af = AgenteFuncional(funcion="F3", tenant_id="test")
        assert af.identidad == "AF-F3"
        assert af.funcion == "F3"

    def test_organismo_bus_percepcion(self):
        from organismo.percepcion.bus import BusPercepcion, SensorBase
        bus = BusPercepcion(tenant_id="test")
        assert len(bus.sensores) == 0

    def test_organismo_circuito_gomas(self):
        from organismo.meta.circuito_gomas import CircuitoGomas, EstadoGoma
        c = CircuitoGomas(tenant_id="test")
        assert len(c.gomas) == 7  # G1-G6 + META
        assert all(g.estado == EstadoGoma.DORMIDA for g in c.gomas.values())


# ============================================================
# SPRINT 4: Director + Enjambre + Cluster
# ============================================================

class TestSprint4Director:
    """Sprint 4: Director orquestador."""

    def test_director_import(self):
        from organismo.cognitiva.director import Director, MAPA_FUNCIONES_AGENTES
        assert "F3" in MAPA_FUNCIONES_AGENTES
        d = Director(tenant_id="test")
        assert d.identidad == "director"

    def test_director_extrae_gaps(self):
        from organismo.cognitiva.director import Director
        from organismo.nodo_vivo import Senal

        d = Director(tenant_id="test")
        señales = [Senal(
            origen="pizarra_cognitiva",
            tipo="RESUMEN",
            payload={
                "ultimo_diagnostico": {
                    "scores": {
                        "F3": {"score": 3.0, "objetivo": 7.0, "lente": "salud"},
                        "F1": {"score": 6.5, "objetivo": 7.0, "lente": "salud"},
                        "F6": {"score": 2.0, "objetivo": 7.0, "lente": "continuidad"},
                    }
                }
            },
        )]

        gaps = d._extraer_gaps(señales)
        assert len(gaps) >= 2  # F3 y F6 tienen gap > 0.5
        # F6 tiene mayor gap (5.0) que F3 (4.0)
        gaps_sorted = sorted(gaps, key=lambda g: g.gap, reverse=True)
        assert gaps_sorted[0].funcion == "F6"

    def test_director_fabrica_agentes(self):
        from organismo.cognitiva.director import Director
        d = Director(tenant_id="test")
        af = d._obtener_agente("F3")
        assert af.funcion == "F3"
        # Misma instancia si se pide otra vez
        af2 = d._obtener_agente("F3")
        assert af is af2


class TestSprint4Cluster:
    """Sprint 4: Cluster cognitivo."""

    def test_cluster_import(self):
        from organismo.cognitiva.cluster import (
            ClusterCognitivo, GapInfo, Compositor, Estratega
        )
        gap = GapInfo(funcion="F3", lente="salud", score=3.0, gap=4.0)
        assert gap.prioridad == 5

    def test_cluster_crea_con_agentes(self):
        from organismo.cognitiva.cluster import ClusterCognitivo, GapInfo
        from organismo.agentes.agente_funcional import AgenteFuncional

        gap = GapInfo(funcion="F3", lente="salud", score=3.0, gap=4.0)
        agentes = [
            AgenteFuncional("F3", "test"),
            AgenteFuncional("F1", "test"),
        ]
        cluster = ClusterCognitivo(gap=gap, agentes=agentes, tenant_id="test")
        assert cluster.identidad == "cluster-F3-salud"
        assert len(cluster.agentes) == 2


class TestSprint4Enjambre:
    """Sprint 4: Enjambre cognitivo."""

    def test_enjambre_import(self):
        from organismo.cognitiva.enjambre import Enjambre, MetricasEnjambre
        e = Enjambre(tenant_id="test")
        assert e.identidad == "enjambre"
        assert e.metricas.ciclos_ejecutados == 0

    def test_metricas_enjambre(self):
        from organismo.cognitiva.enjambre import MetricasEnjambre
        from organismo.nodo_vivo import Senal

        m = MetricasEnjambre()
        señales = [
            Senal(origen="test", tipo="PRESCRIPCION",
                  payload={"coste_usd": 0.01, "verificacion_score": 0.85}),
            Senal(origen="test", tipo="PRESCRIPCION",
                  payload={"coste_usd": 0.02, "verificacion_score": 0.90}),
        ]
        m.registrar_ciclo(señales)
        assert m.ciclos_ejecutados == 1
        assert m.prescripciones_emitidas == 2
        assert m.coste_total_usd == pytest.approx(0.03)
        assert m.score_promedio > 0


# ============================================================
# SPRINT 5: Multi-tenant + Onboarding
# ============================================================

class TestSprint5TenantContext:
    """Sprint 5: Tenant context."""

    def test_tenant_context_import(self):
        from tenant.tenant_context import (
            get_tenant_id, set_tenant_id, TenantContext, with_tenant
        )
        assert callable(get_tenant_id)

    def test_tenant_context_default(self):
        from tenant.tenant_context import get_tenant_id
        assert get_tenant_id() == "default"

    def test_tenant_context_set_reset(self):
        from tenant.tenant_context import get_tenant_id, set_tenant_id
        token = set_tenant_id("pilates")
        assert get_tenant_id() == "pilates"
        # Reset
        from contextvars import copy_context
        import tenant.tenant_context as tc
        tc._tenant_var.reset(token)
        assert get_tenant_id() == "default"

    def test_tenant_context_sync(self):
        from tenant.tenant_context import TenantContext, get_tenant_id
        with TenantContext("dental_001"):
            assert get_tenant_id() == "dental_001"
        assert get_tenant_id() == "default"

    def test_tenant_context_async(self):
        from tenant.tenant_context import TenantContext, get_tenant_id

        async def _test():
            async with TenantContext("saas_001"):
                assert get_tenant_id() == "saas_001"
            assert get_tenant_id() == "default"

        asyncio.get_event_loop().run_until_complete(_test())


class TestSprint5Onboarding:
    """Sprint 5: Onboarding de tenants."""

    def test_onboarding_import(self):
        from tenant.onboarding import onboarding_tenant, SEEDS_SECTOR
        assert "wellness" in SEEDS_SECTOR
        assert "dental" in SEEDS_SECTOR
        assert "saas" in SEEDS_SECTOR

    def test_seeds_sector_structure(self):
        from tenant.onboarding import SEEDS_SECTOR
        for sector, recetas in SEEDS_SECTOR.items():
            for funcion, data in recetas.items():
                assert "receta" in data
                assert "efectividad_base" in data
                assert funcion.startswith("F")


# ============================================================
# SPRINT 6: Frontend + Infra
# ============================================================

class TestSprint6Frontend:
    """Sprint 6: API endpoints cockpit."""

    def test_router_cockpit_import(self):
        from frontend.api.router_cockpit import router
        # Verificar que tiene rutas
        routes = [r.path for r in router.routes]
        assert "/cockpit/estado" in routes or "/estado" in routes

    def test_router_admin_import(self):
        from frontend.api.router_admin import router, OnboardingRequest
        req = OnboardingRequest(
            tenant_id="test", nombre="Test", sector="wellness")
        assert req.tenant_id == "test"


class TestSprint6Infra:
    """Sprint 6: Infra y health checks."""

    def test_health_import(self):
        from infra.health import router
        routes = [r.path for r in router.routes]
        assert "/health" in routes

    def test_app_factory_import(self):
        from infra.app import create_app
        assert callable(create_app)


class TestSprint6CronOrganismo:
    """Sprint 6: Cron integrador."""

    def test_cron_organismo_import(self):
        from organismo.ejecutiva.cron_organismo import CronOrganismo
        cron = CronOrganismo(tenant_id="test")
        assert cron.tenant_id == "test"
        assert cron.circuito is not None
        assert cron.director is not None
        assert cron.enjambre is not None

    def test_cron_gomas_registradas(self):
        from organismo.ejecutiva.cron_organismo import CronOrganismo
        cron = CronOrganismo(tenant_id="test")
        # G1, G2, G4 y META deben tener ejecutar != None
        assert cron.circuito.gomas["G1"].ejecutar is not None
        assert cron.circuito.gomas["G2"].ejecutar is not None
        assert cron.circuito.gomas["G4"].ejecutar is not None
        assert cron.circuito.gomas["META"].ejecutar is not None


# ============================================================
# INTEGRACION: Fractalidad NodoVivo
# ============================================================

class TestFractalidadNodoVivo:
    """Verifica que todos los NodoVivo implementan la interfaz correctamente."""

    def test_agente_es_nodo_vivo(self):
        from organismo.agentes.agente_funcional import AgenteFuncional
        from organismo.nodo_vivo import NodoVivo
        assert issubclass(AgenteFuncional, NodoVivo)

    def test_cluster_es_nodo_vivo(self):
        from organismo.cognitiva.cluster import ClusterCognitivo
        from organismo.nodo_vivo import NodoVivo
        assert issubclass(ClusterCognitivo, NodoVivo)

    def test_director_es_nodo_vivo(self):
        from organismo.cognitiva.director import Director
        from organismo.nodo_vivo import NodoVivo
        assert issubclass(Director, NodoVivo)

    def test_enjambre_es_nodo_vivo(self):
        from organismo.cognitiva.enjambre import Enjambre
        from organismo.nodo_vivo import NodoVivo
        assert issubclass(Enjambre, NodoVivo)

    def test_todos_implementan_4_metodos(self):
        """Todos los NodoVivo concretos implementan percibir/procesar/actuar/aprender."""
        from organismo.agentes.agente_funcional import AgenteFuncional
        from organismo.cognitiva.cluster import ClusterCognitivo
        from organismo.cognitiva.director import Director
        from organismo.cognitiva.enjambre import Enjambre

        for cls in [AgenteFuncional, Director, Enjambre]:
            for method in ["percibir", "procesar", "actuar", "aprender"]:
                assert hasattr(cls, method), f"{cls.__name__} falta {method}"
                # No debe ser abstracto
                import inspect
                assert not getattr(getattr(cls, method), "__isabstractmethod__", False), \
                    f"{cls.__name__}.{method} sigue abstracto"


# ============================================================
# ECOSISTEMA: Cross-tenant
# ============================================================

class TestEcosistema:
    """Ecosistema importa y sus dataclasses funcionan."""

    def test_registry_import(self):
        from ecosistema.registry import TenantConfig, TelemetriaOrganismo
        config = TenantConfig(
            tenant_id="test", nombre="Test", sector="wellness")
        assert config.activo is True

    def test_cross_tenant_import(self):
        from ecosistema.cross_tenant import MotorTransferencia, Transferencia
        t = Transferencia(
            origen_tenant="a", destino_tenant="b",
            gap="F3_baja", receta={"test": True},
            similaridad=0.90, confianza=0.85,
            evidencia="test", requiere_cr1=True,
        )
        assert t.requiere_cr1 is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
