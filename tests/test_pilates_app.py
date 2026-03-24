"""Tests del Exocortex Pilates como App del OS.

Verifica que todas las piezas importan y conectan correctamente.
No requiere DB ni LLM.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest


class TestManifiesto:
    def test_manifiesto_pilates(self):
        from tenant.pilates.app import MANIFIESTO
        assert MANIFIESTO.app_id == "authentic_pilates"
        assert MANIFIESTO.sector == "wellness"
        assert MANIFIESTO.propietario == "Jesus Fernandez"
        assert "F3" in MANIFIESTO.funciones_activas
        assert "diagnostico_acd" in MANIFIESTO.capabilities
        assert "motor.pensar" in MANIFIESTO.requirements

    def test_manifiesto_serializable(self):
        from tenant.pilates.app import MANIFIESTO
        d = MANIFIESTO.to_dict()
        assert d["sector"] == "wellness"
        assert d["presupuesto_llm_semanal"] == 5.0


class TestSandbox:
    def test_sandbox_pilates(self):
        from tenant.pilates.app import SANDBOX
        from ecosistema.apps.sandbox import Entitlement
        assert SANDBOX.app_id == "authentic_pilates"
        assert SANDBOX.verificar(Entitlement.MOTOR_PENSAR)
        assert SANDBOX.verificar(Entitlement.ESCRIBIR_PIZARRA)
        assert not SANDBOX.verificar(Entitlement.CR1_FRENAR)

    def test_sandbox_pizarras(self):
        from tenant.pilates.app import SANDBOX
        assert SANDBOX.puede_acceder_pizarra("cognitiva")
        assert SANDBOX.puede_acceder_pizarra("estado", escritura=True)


class TestActivacion:
    def test_activacion_pilates(self):
        from tenant.pilates.app import ACTIVACION
        assert ACTIVACION.app_id == "authentic_pilates"
        assert len(ACTIVACION.eventos) >= 8

    def test_activacion_lunes(self):
        from tenant.pilates.app import ACTIVACION
        assert ACTIVACION.debe_activar({"hora": "lunes-06:00"})

    def test_activacion_topic(self):
        from tenant.pilates.app import ACTIVACION
        assert ACTIVACION.debe_activar({"topics": ["pilates"]})
        assert ACTIVACION.debe_activar({"topics": ["clientes"]})
        assert not ACTIVACION.debe_activar({"topics": ["finanzas"]})

    def test_activacion_evento(self):
        from tenant.pilates.app import ACTIVACION
        assert ACTIVACION.debe_activar({"evento": "cancelacion"})
        assert ACTIVACION.debe_activar({"evento": "nuevo_cliente"})
        assert not ACTIVACION.debe_activar({"evento": "deploy"})

    def test_activacion_mencion(self):
        from tenant.pilates.app import ACTIVACION
        assert ACTIVACION.debe_activar({"menciones": ["@pilates"]})


class TestSensores:
    def test_bus_completo(self):
        from tenant.pilates.sensores import crear_bus_pilates
        bus = crear_bus_pilates()
        assert len(bus.sensores) >= 13  # 10 SQL + 3 pizarra

    def test_sensores_por_fuente(self):
        from tenant.pilates.sensores import crear_bus_pilates
        bus = crear_bus_pilates()
        por_fuente = bus.sensores_por_fuente
        assert "exterocepcion" in por_fuente
        assert "interocepcion" in por_fuente
        assert "propiocepcion_motora" in por_fuente
        assert len(por_fuente["exterocepcion"]) >= 8

    def test_sensor_fantasmas(self):
        from tenant.pilates.sensores import SENSOR_FANTASMAS
        assert SENSOR_FANTASMAS.nombre == "clientes_fantasma"
        assert SENSOR_FANTASMAS.prioridad == 2
        assert "21 days" in SENSOR_FANTASMAS.query

    def test_sensor_depuracion(self):
        from tenant.pilates.sensores import SENSOR_GRUPOS_INFRAUTILIZADOS
        assert SENSOR_GRUPOS_INFRAUTILIZADOS.tipo_senal == "OPORTUNIDAD"
        assert "inscritos" in SENSOR_GRUPOS_INFRAUTILIZADOS.query


class TestPrompts:
    def test_prompts_completos(self):
        from tenant.pilates.prompts import PROMPTS_AF
        assert len(PROMPTS_AF) == 7
        for f in ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]:
            assert f in PROMPTS_AF
            assert len(PROMPTS_AF[f]) > 100

    def test_prompt_f3_diferenciador(self):
        from tenant.pilates.prompts import PROMPTS_AF
        assert "DIFERENCIADOR NUCLEAR" in PROMPTS_AF["F3"]
        assert "VETO" in PROMPTS_AF["F3"]

    def test_tono_albelda(self):
        from tenant.pilates.prompts import TONO_ALBELDA
        assert "Albelda" in TONO_ALBELDA
        assert "tutea" in TONO_ALBELDA.lower()

    def test_contexto_negocio(self):
        from tenant.pilates.prompts import CONTEXTO_NEGOCIO
        assert "22 clientes" in CONTEXTO_NEGOCIO
        assert "EEDAP" in CONTEXTO_NEGOCIO
        assert "87%" in CONTEXTO_NEGOCIO


class TestRecetas:
    def test_recetas_completas(self):
        from tenant.pilates.recetas import RECETAS_PILATES
        assert len(RECETAS_PILATES) >= 9

    def test_receta_estructura(self):
        from tenant.pilates.recetas import RECETAS_PILATES
        for clave, receta in RECETAS_PILATES.items():
            assert "funcion" in receta
            assert "nombre" in receta
            assert "descripcion" in receta
            assert "accion" in receta
            assert "efectividad_base" in receta
            assert "requiere_cr1" in receta
            assert receta["funcion"].startswith("F")

    def test_receta_cr1_depuracion(self):
        from tenant.pilates.recetas import RECETAS_PILATES
        cerrar = RECETAS_PILATES["F3_cerrar_grupo_vacio"]
        assert cerrar["requiere_cr1"] is True
        assert cerrar["efectividad_base"] >= 0.7

    def test_recetas_por_funcion(self):
        from tenant.pilates.recetas import RECETAS_PILATES
        funciones = set(r["funcion"] for r in RECETAS_PILATES.values())
        assert "F1" in funciones
        assert "F2" in funciones
        assert "F3" in funciones


class TestOrganismo:
    def test_crear_organismo(self):
        from tenant.pilates.organismo import crear_organismo_pilates
        cron = crear_organismo_pilates()
        assert cron.tenant_id == "authentic_pilates"
        assert cron.director is not None
        assert cron.enjambre is not None
        assert cron.circuito is not None

    def test_organismo_gomas_registradas(self):
        from tenant.pilates.organismo import crear_organismo_pilates
        cron = crear_organismo_pilates()
        assert cron.circuito.gomas["G1"].ejecutar is not None
        assert cron.circuito.gomas["G2"].ejecutar is not None
        assert cron.circuito.gomas["META"].ejecutar is not None

    def test_organismo_prompts_inyectados(self):
        from tenant.pilates.organismo import crear_organismo_pilates
        cron = crear_organismo_pilates()
        # Director debe tener prompts
        af3 = cron.director._obtener_agente("F3")
        assert "DEPURACIÓN" in af3.system_prompt or "DEPURACION" in af3.system_prompt

    def test_sensor_queries_inyectadas(self):
        from tenant.pilates.organismo import SENSOR_QUERIES_AF
        assert "F1" in SENSOR_QUERIES_AF
        assert "fantasmas" in SENSOR_QUERIES_AF["F1"]
        assert "F3" in SENSOR_QUERIES_AF
        assert "infrautilizados" in SENSOR_QUERIES_AF["F3"]


class TestDurableObject:
    def test_durable_object_pilates(self):
        from tenant.pilates.app import DURABLE_OBJECT
        assert DURABLE_OBJECT.tenant_id == "authentic_pilates"
        assert not DURABLE_OBJECT.activo
        DURABLE_OBJECT.activar()
        assert DURABLE_OBJECT.activo
        DURABLE_OBJECT.dormir()


class TestIntegracion:
    """Verifica que todas las piezas conectan end-to-end."""

    def test_manifiesto_a_sandbox(self):
        from tenant.pilates.app import MANIFIESTO, SANDBOX
        assert MANIFIESTO.app_id == SANDBOX.app_id

    def test_sensores_a_organismo(self):
        from tenant.pilates.sensores import TENANT_ID as S_TID
        from tenant.pilates.organismo import TENANT_ID as O_TID
        assert S_TID == O_TID == "authentic_pilates"

    def test_prompts_cubren_funciones(self):
        from tenant.pilates.prompts import PROMPTS_AF
        from tenant.pilates.app import MANIFIESTO
        for f in MANIFIESTO.funciones_activas:
            assert f in PROMPTS_AF, f"Falta prompt para {f}"

    def test_recetas_cubren_gaps(self):
        from tenant.pilates.recetas import RECETAS_PILATES
        funciones_con_receta = set(r["funcion"] for r in RECETAS_PILATES.values())
        # Al menos F1, F2, F3 deben tener recetas (son los gaps criticos)
        assert "F1" in funciones_con_receta
        assert "F2" in funciones_con_receta
        assert "F3" in funciones_con_receta


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
