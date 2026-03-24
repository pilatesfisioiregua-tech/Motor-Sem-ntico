"""Apps — Lifecycle de exocortex como aplicaciones del OS.

Cada exocortex es una App que:
  - Se instala con un Manifiesto (sector, capabilities, requirements)
  - Usa servicios del OS (motor.pensar, pizarras, bus)
  - Tiene su propio espacio de memoria (/home/{tenant_id}/)
  - Puede publicar recetas exitosas al App Store
  - Puede recibir recetas del App Store via IPC

Lifecycle:
  INSTALACION → CONFIGURACION → EJECUCION ⟲ → PAUSA/RESUME → DESINSTALACION
"""
