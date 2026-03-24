"""OS — Sistema Operativo de OMNI-MIND.

Componentes:
  kernel_os.py  → Kernel del OS: boot, shutdown, tabla de procesos
  scheduler.py  → Planificador: decide cuando ejecutar cada app
  proceso.py    → Proceso: un exocortex en ejecucion (wrapper del Enjambre)
  ipc.py        → IPC: comunicacion entre apps (transferencias cross-dominio)
  app_store.py  → App Store: catalogo de recetas transferibles

Analogias con un OS real:
  Scheduler  = cron + prioridades + presupuesto (como nice/ionice)
  Proceso    = pid + estado + memoria asignada
  IPC        = pipes entre procesos (transferencias Ley 10 TCF)
  App Store  = repositorio de recetas exitosas cross-dominio
  Signals    = LISTEN/NOTIFY de PostgreSQL (como SIGTERM, SIGUSR1)
"""
