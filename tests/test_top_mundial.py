"""Tests de los 22 conceptos top mundial implementados.

Verifica imports, instanciacion y logica basica de cada concepto.
No requiere DB ni LLM.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest


# ============================================================
# MOTOR: Proveedores + Circuit Breaker + Cascade
# ============================================================

class TestProveedoresMotor:
    def test_miniport_interface(self):
        from motor.proveedores import Miniport, RespuestaLLM
        assert hasattr(Miniport, "enviar")

    def test_miniport_openrouter(self):
        from motor.proveedores import MiniportOpenRouter
        mp = MiniportOpenRouter()
        assert mp.soporta("openai/gpt-4o")
        assert mp.soporta("anthropic/claude-opus-4")
        assert not mp.soporta("local/llama")

    def test_miniport_local(self):
        from motor.proveedores import MiniportLocal
        mp = MiniportLocal()
        assert mp.soporta("local/llama3")
        assert not mp.soporta("openai/gpt-4o")

    def test_circuit_breaker_estados(self):
        from motor.proveedores import CircuitBreaker, EstadoBreaker
        cb = CircuitBreaker(nombre="test", max_errores=2, cooldown_seg=0.1)

        assert cb.estado == EstadoBreaker.CLOSED
        assert cb.puede_pasar()

        cb.registrar_error()
        assert cb.estado == EstadoBreaker.CLOSED  # 1 error, aun no abre

        cb.registrar_error()
        assert cb.estado == EstadoBreaker.OPEN  # 2 errores → abre

        assert not cb.puede_pasar()  # Bloqueado

        time.sleep(0.15)  # Esperar cooldown
        assert cb.puede_pasar()  # Half-open
        assert cb.estado == EstadoBreaker.HALF_OPEN

        cb.registrar_exito()
        assert cb.estado == EstadoBreaker.CLOSED  # Recuperado

    def test_quality_gate(self):
        from motor.proveedores import quality_gate
        assert quality_gate("", funcion="F3") == 0.0  # Vacio
        assert quality_gate("a" * 10) == 0.0  # Muy corto
        score = quality_gate("Esta es una respuesta detallada con contenido util " * 3)
        assert score > 0.5

    def test_cascade_cadenas(self):
        from motor.proveedores import CADENA_CASCADE, UMBRAL_QUALITY_GATE
        assert len(CADENA_CASCADE["media"]) == 2
        assert len(CADENA_CASCADE["alta"]) == 2
        assert UMBRAL_QUALITY_GATE["alta"] > UMBRAL_QUALITY_GATE["baja"]

    def test_motor_proveedores_singleton(self):
        from motor.proveedores import get_motor_proveedores
        mp = get_motor_proveedores()
        assert "openrouter" in mp.miniports

    def test_estimar_coste(self):
        from motor.proveedores import _estimar_coste
        coste = _estimar_coste("deepseek/deepseek-v3.2", 1000, 500)
        assert coste < 0.01  # DeepSeek es barato


# ============================================================
# KERNEL: Capabilities
# ============================================================

class TestCapabilities:
    def test_capability_crear(self):
        from kernel.capabilities import CapabilityManager, Permiso, TipoRecurso
        mgr = CapabilityManager()
        cap = mgr.crear("AF-F3", "pizarra_cognitiva", TipoRecurso.PIZARRA,
                        Permiso.LECTURA)
        assert cap.titular == "AF-F3"
        assert cap.permite(Permiso.LEER)
        assert not cap.permite(Permiso.ESCRIBIR)

    def test_capability_atenuar(self):
        from kernel.capabilities import CapabilityManager, Permiso, TipoRecurso
        mgr = CapabilityManager()
        cap = mgr.crear("director", "motor", TipoRecurso.MOTOR,
                        Permiso.COMPLETO, delegable=True)

        # Atenuar: de COMPLETO a solo LECTURA
        atenuada = mgr.atenuar(cap, Permiso.LECTURA, "AF-F1")
        assert atenuada is not None
        assert atenuada.permite(Permiso.LEER)
        assert not atenuada.permite(Permiso.ESCRIBIR)

    def test_capability_revocar(self):
        from kernel.capabilities import CapabilityManager, Permiso, TipoRecurso
        mgr = CapabilityManager()
        cap = mgr.crear("test", "recurso", TipoRecurso.PIZARRA, Permiso.LECTURA)
        assert mgr.verificar(cap, Permiso.LEER)

        mgr.revocar(cap.token)
        assert not mgr.verificar(cap, Permiso.LEER)

    def test_capability_scope(self):
        from kernel.capabilities import CapabilityManager, Permiso, TipoRecurso
        mgr = CapabilityManager()
        cap = mgr.crear("AF-F3", "pizarra", TipoRecurso.PIZARRA,
                        Permiso.LECTURA,
                        scope={"tenant_id": "pilates", "tipo": "cognitiva"})

        assert cap.cubre_scope(tenant_id="pilates", tipo="cognitiva")
        assert not cap.cubre_scope(tenant_id="dental", tipo="cognitiva")


# ============================================================
# KERNEL: Probes (eBPF cognitivo)
# ============================================================

class TestProbes:
    def test_probes_registrar(self):
        from kernel.probes import SistemaProbes, ProbeResult
        sp = SistemaProbes()

        def mi_probe(datos):
            return ProbeResult(probe_id="test", checkpoint="post_pensar")

        pid = sp.registrar("post_pensar", mi_probe, probe_id="test")
        assert pid == "test"

    def test_probes_ejecutar(self):
        from kernel.probes import SistemaProbes, ProbeResult
        sp = SistemaProbes()

        resultados_capturados = []

        def probe_observar(datos):
            resultados_capturados.append(datos)
            return ProbeResult(probe_id="obs", checkpoint="post_pensar",
                               datos=datos)

        sp.registrar("post_pensar", probe_observar, probe_id="obs")
        results = sp.ejecutar("post_pensar", {"modelo": "gpt-4o"})

        assert len(results) == 1
        assert resultados_capturados[0] == {"modelo": "gpt-4o"}

    def test_probes_alerta(self):
        from kernel.probes import SistemaProbes, ProbeResult
        sp = SistemaProbes()

        def probe_alertar(datos):
            return ProbeResult(probe_id="alerta", checkpoint="on_error",
                               alerta="Score muy bajo!")

        sp.registrar("on_error", probe_alertar)
        results = sp.ejecutar("on_error")
        assert results[0].alerta == "Score muy bajo!"

    def test_probes_checkpoint_invalido(self):
        from kernel.probes import SistemaProbes
        sp = SistemaProbes()
        with pytest.raises(ValueError):
            sp.registrar("checkpoint_falso", lambda x: x)


# ============================================================
# KERNEL: cgroups + namespaces
# ============================================================

class TestCgroups:
    def test_cgroup_limites(self):
        from kernel.cgroups import Cgroup, LimitesRecurso
        cg = Cgroup(nombre="AF-F3", limites=LimitesRecurso(tokens_por_ciclo=1000))
        assert cg.puede_usar_tokens(500)
        cg.registrar_tokens(500)
        assert cg.puede_usar_tokens(400)
        assert not cg.puede_usar_tokens(600)

    def test_cgroup_throttle(self):
        from kernel.cgroups import Cgroup, LimitesRecurso
        cg = Cgroup(nombre="test", limites=LimitesRecurso(tokens_por_ciclo=100))
        cg.registrar_tokens(95)  # >90% → throttle
        assert cg.throttled

    def test_namespace(self):
        from kernel.cgroups import Namespace
        ns = Namespace(nombre="pilates", tenant_id="pilates_001")
        assert ns.puede_acceder("cognitiva")
        assert ns.puede_acceder("estado", escritura=True)

    def test_namespace_readonly(self):
        from kernel.cgroups import Namespace
        ns = Namespace(nombre="readonly", tenant_id="t1", solo_lectura=True)
        assert ns.puede_acceder("estado")
        assert not ns.puede_acceder("estado", escritura=True)

    def test_gestor_perfiles(self):
        from kernel.cgroups import GestorRecursos
        gr = GestorRecursos()
        cg = gr.crear_cgroup("AF-F3", perfil="critico")
        assert cg.limites.tokens_por_ciclo == 100_000

        cg_bg = gr.crear_cgroup("cleanup", perfil="background")
        assert cg_bg.limites.tokens_por_ciclo == 10_000


# ============================================================
# MEMORIA: Cache TLB
# ============================================================

class TestCacheTLB:
    def test_cache_basico(self):
        from ecosistema.memoria.cache_tlb import CacheTLB
        c = CacheTLB(max_entradas=5)
        c.put("t1", "estado", "gomas", {"G1": "girando"})
        assert c.get("t1", "estado", "gomas") == {"G1": "girando"}
        assert c.get("t1", "estado", "inexistente") is None

    def test_cache_hit_rate(self):
        from ecosistema.memoria.cache_tlb import CacheTLB
        c = CacheTLB()
        c.put("t1", "estado", "k1", "v1")
        c.get("t1", "estado", "k1")  # hit
        c.get("t1", "estado", "k2")  # miss
        assert c.stats["hit_rate"] == 0.5

    def test_cache_eviccion(self):
        from ecosistema.memoria.cache_tlb import CacheTLB
        c = CacheTLB(max_entradas=2)
        c.put("t1", "a", "1", "v1")
        c.put("t1", "a", "2", "v2")
        c.put("t1", "a", "3", "v3")  # Evicta una
        assert c.stats["entradas"] == 2


# ============================================================
# MEMORIA: Copy-on-Write
# ============================================================

class TestCopyOnWrite:
    def test_branch_crear(self):
        from ecosistema.memoria.cow import GestorBranches
        gb = GestorBranches("pilates")
        br = gb.fork("experimento_F3", "Probar nueva receta")
        assert br.nombre == "experimento_F3"
        assert br.n_cambios == 0

    def test_branch_escribir(self):
        from ecosistema.memoria.cow import GestorBranches
        gb = GestorBranches("pilates")
        br = gb.fork("test")
        gb.escribir(br.id, "cognitiva", "receta_F3", {"nueva": True})
        assert br.n_cambios == 1

    def test_branch_diff(self):
        from ecosistema.memoria.cow import GestorBranches
        gb = GestorBranches("t1")
        br = gb.fork("test")
        gb.escribir(br.id, "estado", "gomas", {"G1": "modificado"})
        diff = gb.diff(br.id)
        assert diff["n_cambios"] == 1
        assert "estado/gomas" in diff["cambios"]

    def test_branch_descartar(self):
        from ecosistema.memoria.cow import GestorBranches
        gb = GestorBranches("t1")
        br = gb.fork("descartable")
        gb.descartar(br.id)
        assert br.cerrado
        assert br.resultado == "descartado"


# ============================================================
# MEMORIA: Event Sourcing
# ============================================================

class TestEventSourcing:
    def test_evento_crear(self):
        from ecosistema.memoria.event_sourcing import EventoCognitivo
        ev = EventoCognitivo(
            tipo_evento="ConocimientoCreado",
            tenant_id="pilates",
            agente="AF-F3",
            datos={"tipo": "cognitiva", "clave": "receta_F3", "valor": {}},
        )
        assert ev.tipo_evento == "ConocimientoCreado"
        assert ev.version == 1


# ============================================================
# MEMORIA: Grafo
# ============================================================

class TestGrafo:
    def test_tipos_relacion(self):
        from ecosistema.memoria.grafo import TIPOS_RELACION
        assert "DEPENDE_DE" in TIPOS_RELACION
        assert "USA" in TIPOS_RELACION
        assert "CONFLICTO" in TIPOS_RELACION

    def test_grafo_crear(self):
        from ecosistema.memoria.grafo import GrafoConocimiento
        g = GrafoConocimiento("pilates")
        assert g.tenant_id == "pilates"


# ============================================================
# MEMORIA: Busqueda Hibrida
# ============================================================

class TestBusquedaHibrida:
    def test_busqueda_crear(self):
        from ecosistema.memoria.busqueda_hibrida import BusquedaHibrida
        bh = BusquedaHibrida("pilates", alpha=0.7)
        assert bh.alpha == 0.7


# ============================================================
# IPC: Control Plane + Federated + Contract Net + Discovery + AppStore
# ============================================================

class TestIPCAvanzado:
    def test_bus_ipc_control_plane(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC, TipoMensaje
        bus = BusIPC()

        recibido = []
        bus.registrar_handler_control(
            TipoMensaje.SIGNAL_PAUSE,
            lambda msg: recibido.append(msg))

        bus.enviar(MensajeIPC(
            origen_pid="os", destino_pid="pilates",
            tipo=TipoMensaje.SIGNAL_PAUSE))

        assert len(recibido) == 1  # Procesado inmediatamente

    def test_bus_ipc_data_plane(self):
        from ecosistema.os.ipc import BusIPC, MensajeIPC, TipoMensaje
        bus = BusIPC()

        bus.enviar(MensajeIPC(
            origen_pid="pilates", destino_pid="dental",
            tipo=TipoMensaje.DATA_RECETA,
            payload={"receta": "NPS"}))

        msgs = bus.recibir("dental")
        assert len(msgs) == 1
        assert msgs[0].payload["receta"] == "NPS"

    def test_federated_learning(self):
        from ecosistema.os.ipc import FederatedLearning, GradienteReceta
        fl = FederatedLearning()

        fl.publicar_gradiente(GradienteReceta(
            gap="F3_baja", sector="wellness", tamano="micro",
            receta_tipo="NPS_trimestral", tasa_cierre=0.82,
            n_ejecuciones=50, ciclos_para_cerrar=3,
            contexto_gap="F3 score 3/10"))

        mejor = fl.mejor_receta_para("F3_baja", sector="wellness")
        assert mejor is not None
        assert mejor.tasa_cierre == 0.82

    def test_contract_net(self):
        from ecosistema.os.ipc import ContractNet
        cn = ContractNet()
        sub = cn.crear_subasta("Cerrar F3", "F3_baja")
        sub.pujar("AF-F3", competencia=0.9, coste_estimado=0.05, tiempo_estimado_min=5)
        sub.pujar("AF-F1", competencia=0.6, coste_estimado=0.03, tiempo_estimado_min=3)

        ganador = sub.adjudicar()
        assert ganador == "AF-F3"  # Mayor competencia

    def test_discovery(self):
        from ecosistema.os.ipc import Discovery, ServicioRegistrado
        disc = Discovery()
        disc.registrar(ServicioRegistrado(
            agente_id="AF-F3", nombre="depuracion",
            capacidades=["F3", "depuracion", "NPS"]))

        encontrados = disc.buscar("F3")
        assert len(encontrados) == 1
        assert encontrados[0].agente_id == "AF-F3"

    def test_appstore_quality_gate(self):
        from ecosistema.os.ipc import AppStoreCurado
        store = AppStoreCurado()

        # Rechazada: pocas ejecuciones
        rid = store.publicar("test", "F3_baja", "wellness",
                             {"accion": "NPS"}, 0.9, 2)
        assert rid is None

        # Aceptada
        rid = store.publicar("NPS Trimestral", "F3_baja", "wellness",
                             {"accion": "NPS cada 3 meses"}, 0.82, 50)
        assert rid is not None

        resultados = store.buscar("F3_baja")
        assert len(resultados) == 1

    def test_appstore_confianza(self):
        from ecosistema.os.ipc import RecetaPublicada
        r = RecetaPublicada(
            id="r1", nombre="test", gap="F3_baja", sector="wellness",
            tasa_cierre=0.85, n_ejecuciones=60, n_tenants_exitosos=3)
        assert r.confianza > 0.85  # Base + multi-tenant + volumen


# ============================================================
# APPS: Sandbox + Intents + Hooks + Activation + Durable Objects
# ============================================================

class TestAppsAvanzado:
    def test_sandbox_entitlements(self):
        from ecosistema.apps.sandbox import Sandbox, Entitlement
        sb = Sandbox(app_id="pilates", tenant_id="t1",
                     entitlements=Entitlement.BASICO)
        assert sb.verificar(Entitlement.LEER_PIZARRA)
        assert sb.verificar(Entitlement.MOTOR_PENSAR)
        assert not sb.verificar(Entitlement.CR1_FRENAR)

    def test_sandbox_paquetes(self):
        from ecosistema.apps.sandbox import Entitlement
        assert Entitlement.LEER_PIZARRA in Entitlement.BASICO
        assert Entitlement.MOTOR_PENSAR in Entitlement.STANDARD
        assert Entitlement.CR1_FRENAR in Entitlement.ADMIN

    def test_intents_routing(self):
        from ecosistema.apps.sandbox import Intent, IntentRouter
        router = IntentRouter()
        router.registrar_handler("analisis_legal", "diagnosticar",
                                 ["caso_clinico", "negocio"])
        router.registrar_handler("pilates_af3", "diagnosticar",
                                 ["negocio"])

        intent = Intent(action="diagnosticar", data_type="negocio")
        receptores = router.resolver(intent)
        assert len(receptores) == 2

    def test_durable_objects(self):
        from ecosistema.apps.sandbox import DurableObject
        do = DurableObject(id="pilates_001", tenant_id="pilates",
                           app_id="wellness")
        assert not do.activo

        do.activar()
        assert do.activo

        do.put("contexto", {"clientes": 22})
        assert do.get("contexto") == {"clientes": 22}

        do.dormir()
        assert not do.activo

    def test_hooks_actions(self):
        from ecosistema.apps.sandbox import SistemaHooks
        sh = SistemaHooks()

        resultados = []
        sh.add_action("after_ciclo", "compliance",
                       lambda datos: resultados.append(datos))

        sh.do_action("after_ciclo", {"score": 0.85})
        assert len(resultados) == 1
        assert resultados[0]["score"] == 0.85

    def test_hooks_filters(self):
        from ecosistema.apps.sandbox import SistemaHooks
        sh = SistemaHooks()

        sh.add_filter("before_response", "censor",
                       lambda texto: texto.upper())

        resultado = sh.apply_filters("before_response", "hola mundo")
        assert resultado == "HOLA MUNDO"

    def test_activation_events(self):
        from ecosistema.apps.sandbox import ReglasActivacion, GestorActivacion
        ga = GestorActivacion()

        ga.registrar(ReglasActivacion(
            app_id="legal",
            eventos=[{"tipo": "onTopic", "valor": "compliance"}]))

        ga.registrar(ReglasActivacion(
            app_id="finanzas",
            eventos=[{"tipo": "onTopic", "valor": "rentabilidad"}]))

        apps = ga.apps_a_activar({"topics": ["compliance"]})
        assert "legal" in apps
        assert "finanzas" not in apps


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
