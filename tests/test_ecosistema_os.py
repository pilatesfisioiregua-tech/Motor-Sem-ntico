"""Tests del ecosistema como Sistema Operativo.

Verifica:
  - Memoria (Almacen) importa y funciona como VFS
  - OS (KernelOS, Scheduler, Proceso) importan y conectan
  - IPC (BusIPC, AppStore) importan y funcionan
  - Apps (Manifiesto) importan y serializan
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ============================================================
# MEMORIA (Filesystem)
# ============================================================

class TestMemoria:
    def test_almacen_import(self):
        from ecosistema.memoria.almacen import Almacen, ArchivoMemoria
        a = Almacen("test_tenant")
        assert a.tenant_id == "test_tenant"

    def test_archivo_memoria(self):
        from ecosistema.memoria.almacen import ArchivoMemoria
        f = ArchivoMemoria(
            tenant_id="t1", tipo="estado", clave="gomas",
            valor={"G1": "girando"})
        assert f.tipo == "estado"
        assert f.ttl_horas == 0

    def test_almacen_os(self):
        from ecosistema.memoria.almacen import Almacen
        a = Almacen("os")
        assert a.tenant_id == "os"


# ============================================================
# OS - PROCESO
# ============================================================

class TestProceso:
    def test_proceso_import(self):
        from ecosistema.os.proceso import Proceso, EstadoProceso
        p = Proceso(pid="pilates_001", app_id="wellness_pilates",
                    nombre="Authentic Pilates", sector="wellness")
        assert p.estado == EstadoProceso.CREADO
        assert p.salud == "ok"

    def test_proceso_pausar_reanudar(self):
        from ecosistema.os.proceso import Proceso, EstadoProceso
        p = Proceso(pid="t1", app_id="a1", nombre="Test", sector="test")
        p.estado = EstadoProceso.DORMIDO  # simular que ya arranco

        p.pausar()
        assert p.estado == EstadoProceso.PAUSADO
        assert p.salud == "pausado"

        p.reanudar()
        assert p.estado == EstadoProceso.DORMIDO

    def test_proceso_presupuesto(self):
        from ecosistema.os.proceso import Proceso
        p = Proceso(pid="t1", app_id="a1", nombre="Test", sector="test",
                    presupuesto_semanal=5.0)
        p.presupuesto_gastado = 4.8
        assert p.salud == "presupuesto_bajo"

        p.resetear_presupuesto()
        assert p.presupuesto_gastado == 0.0

    def test_proceso_memoria_lazy(self):
        from ecosistema.os.proceso import Proceso
        p = Proceso(pid="t1", app_id="a1", nombre="Test", sector="test")
        assert p.memoria.tenant_id == "t1"

    def test_proceso_enjambre_lazy(self):
        from ecosistema.os.proceso import Proceso
        p = Proceso(pid="t1", app_id="a1", nombre="Test", sector="test")
        assert p.enjambre.identidad == "enjambre"
        assert p.enjambre.tenant_id == "t1"


# ============================================================
# OS - SCHEDULER
# ============================================================

class TestScheduler:
    def test_scheduler_import(self):
        from ecosistema.os.scheduler import Scheduler
        s = Scheduler()
        assert len(s.procesos) == 0

    def test_scheduler_registrar_listar(self):
        from ecosistema.os.scheduler import Scheduler
        from ecosistema.os.proceso import Proceso, EstadoProceso

        s = Scheduler()
        p1 = Proceso(pid="t1", app_id="a1", nombre="App1", sector="wellness",
                      prioridad=3, estado=EstadoProceso.DORMIDO)
        p2 = Proceso(pid="t2", app_id="a2", nombre="App2", sector="dental",
                      prioridad=7, estado=EstadoProceso.DORMIDO)

        s.registrar(p1)
        s.registrar(p2)

        activos = s.listar_activos()
        assert len(activos) == 2
        # Ordenados por prioridad
        assert activos[0].pid == "t1"  # prioridad 3
        assert activos[1].pid == "t2"  # prioridad 7

    def test_scheduler_terminar(self):
        from ecosistema.os.scheduler import Scheduler
        from ecosistema.os.proceso import Proceso, EstadoProceso

        s = Scheduler()
        p = Proceso(pid="t1", app_id="a1", nombre="App1", sector="test")
        s.registrar(p)
        assert len(s.listar_activos()) == 1

        s.terminar("t1")
        assert len(s.listar_activos()) == 0

    def test_scheduler_stats(self):
        from ecosistema.os.scheduler import Scheduler
        from ecosistema.os.proceso import Proceso, EstadoProceso

        s = Scheduler()
        s.registrar(Proceso(pid="t1", app_id="a1", nombre="A", sector="s",
                            estado=EstadoProceso.DORMIDO, presupuesto_semanal=5.0))
        s.registrar(Proceso(pid="t2", app_id="a2", nombre="B", sector="s",
                            estado=EstadoProceso.EJECUTANDO, presupuesto_semanal=3.0))

        stats = s.stats
        assert stats["total_procesos"] == 2
        assert stats["dormidos"] == 1
        assert stats["ejecutando"] == 1
        assert stats["presupuesto_total"] == 8.0

    def test_scheduler_resetear_presupuestos(self):
        from ecosistema.os.scheduler import Scheduler
        from ecosistema.os.proceso import Proceso

        s = Scheduler()
        p = Proceso(pid="t1", app_id="a1", nombre="A", sector="s")
        p.presupuesto_gastado = 4.5
        s.registrar(p)

        s.resetear_presupuestos()
        assert s.procesos["t1"].presupuesto_gastado == 0.0


# ============================================================
# OS - KERNEL
# ============================================================

class TestKernelOS:
    def test_kernel_os_import(self):
        from ecosistema.os.kernel_os import KernelOS
        k = KernelOS()
        assert k._booted is False
        assert k.scheduler is not None
        assert k.ipc is not None

    def test_kernel_ps(self):
        from ecosistema.os.kernel_os import KernelOS
        from ecosistema.os.proceso import Proceso, EstadoProceso

        k = KernelOS()
        k.scheduler.registrar(
            Proceso(pid="pilates", app_id="wellness_pilates",
                    nombre="Authentic Pilates", sector="wellness",
                    estado=EstadoProceso.DORMIDO))

        ps = k.ps()
        assert len(ps) == 1
        assert ps[0]["pid"] == "pilates"
        assert ps[0]["salud"] == "ok"

    def test_kernel_top(self):
        from ecosistema.os.kernel_os import KernelOS
        k = KernelOS()
        top = k.top()
        assert "total_procesos" in top
        assert "presupuesto_total" in top


# ============================================================
# IPC
# ============================================================

class TestIPC:
    def test_bus_ipc_import(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC
        bus = BusIPC()
        assert bus.mensajes_pendientes == 0

    def test_bus_enviar_recibir(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC

        bus = BusIPC()
        msg = MensajeIPC(
            origen_pid="pilates", destino_pid="dental",
            tipo="transferencia", gap="F3_baja",
            payload={"receta": "NPS trimestral"},
            similaridad=0.90, confianza=0.85,
        )
        bus.enviar(msg)
        assert bus.mensajes_pendientes == 1

        recibidos = bus.recibir("dental")
        assert len(recibidos) == 1
        assert recibidos[0].gap == "F3_baja"
        assert bus.mensajes_pendientes == 0

    def test_bus_no_recibe_ajenos(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC

        bus = BusIPC()
        bus.enviar(MensajeIPC(
            origen_pid="a", destino_pid="b",
            tipo="test"))

        recibidos = bus.recibir("c")  # c no tiene mensajes
        assert len(recibidos) == 0
        assert bus.mensajes_pendientes == 1  # sigue en cola para b

    def test_app_store(self):
        from ecosistema.os.ipc import AppStore

        store = AppStore()
        store.publicar(
            receta={"gap": "F3_baja", "accion": "NPS trimestral"},
            evidencia={"confianza": 0.85, "sector": "wellness"})

        resultados = store.buscar("F3_baja")
        assert len(resultados) == 1

        resultados_alta = store.buscar("F3_baja", min_confianza=0.90)
        assert len(resultados_alta) == 0  # 0.85 < 0.90


# ============================================================
# APPS - MANIFIESTO
# ============================================================

class TestApps:
    def test_manifiesto_import(self):
        from ecosistema.apps.manifiesto import AppManifiesto
        m = AppManifiesto(
            app_id="pilates_001",
            nombre="Authentic Pilates",
            sector="wellness",
            propietario="Jesus",
        )
        assert m.app_id == "pilates_001"
        assert "diagnostico_acd" in m.capabilities
        assert "motor.pensar" in m.requirements

    def test_manifiesto_serializar(self):
        from ecosistema.apps.manifiesto import AppManifiesto
        m = AppManifiesto(
            app_id="test", nombre="Test", sector="saas")

        d = m.to_dict()
        assert d["app_id"] == "test"
        assert d["sector"] == "saas"
        assert d["presupuesto_llm_semanal"] == 5.0

    def test_manifiesto_deserializar(self):
        from ecosistema.apps.manifiesto import AppManifiesto
        d = {
            "app_id": "dental_001",
            "nombre": "Clinica Dental",
            "sector": "dental",
            "presupuesto_llm_semanal": 3.0,
        }
        m = AppManifiesto.from_dict(d)
        assert m.sector == "dental"
        assert m.presupuesto_semanal == 3.0


# ============================================================
# INTEGRACION: La metafora completa
# ============================================================

class TestMetaforaOS:
    """Verifica que la metafora OS → Apps → Memoria encaja."""

    def test_kernel_contiene_scheduler(self):
        from ecosistema.os.kernel_os import KernelOS
        k = KernelOS()
        assert hasattr(k, "scheduler")
        assert hasattr(k, "ipc")
        assert hasattr(k, "memoria_os")

    def test_scheduler_contiene_procesos(self):
        from ecosistema.os.scheduler import Scheduler
        s = Scheduler()
        assert hasattr(s, "procesos")
        assert hasattr(s, "ejecutar_ronda")

    def test_proceso_contiene_enjambre_y_memoria(self):
        from ecosistema.os.proceso import Proceso
        p = Proceso(pid="t", app_id="a", nombre="T", sector="s")
        # Lazy init
        assert p.memoria is not None
        assert p.enjambre is not None

    def test_ipc_conecta_apps(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC
        bus = BusIPC()
        bus.enviar(MensajeIPC(
            origen_pid="app_a", destino_pid="app_b",
            tipo="transferencia", gap="F3_baja",
            payload={"receta": "test"},
            requiere_cr1=True))
        msgs = bus.recibir("app_b")
        assert msgs[0].requiere_cr1 is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
