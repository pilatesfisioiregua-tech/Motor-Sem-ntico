"""OMNI-MIND Ecosistema — Sistema Operativo para N exocortex.

Metafora OS:
  DB        = Memoria (filesystem persistente)
  Ecosistema = Sistema Operativo (scheduler, procesos, IPC)
  Exocortex  = App instalada en el OS

Estructura:
  ecosistema/
    memoria/    → Filesystem: almacen unificado DB (pizarras, cache, telemetria)
    os/         → Kernel del OS: scheduler, procesos, IPC, app store
    apps/       → Lifecycle de apps: instalar, actualizar, pausar, desinstalar

Cada App (exocortex) es un proceso del OS que:
  - Se instala con un manifiesto (sector, capabilities, requirements)
  - Usa servicios del OS (motor.pensar, pizarras, bus percepcion)
  - Tiene su propio espacio de memoria (tenant_id en om_pizarra)
  - Se comunica con otras apps via IPC (transferencias cross-dominio)
  - El OS gestiona su ciclo de vida (scheduler, health, presupuesto)

El MOAT: N apps × M ciclos = App Store con recetas entrenadas cross-dominio.
"""
