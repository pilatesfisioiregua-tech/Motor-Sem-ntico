"""Memoria — Filesystem persistente del OS.

La DB es la memoria del sistema operativo. Toda persistencia pasa por aqui.
Cada app tiene su espacio de memoria aislado (tenant_id).

Capas:
  om_pizarra           → Filesystem principal (8 tipos = 8 directorios)
  om_pizarra_cache_llm → Cache de pagina (respuestas LLM reutilizables)
  om_motor_telemetria  → Logs del sistema (metricas de uso)
  om_prescripciones    → Registro de acciones (audit trail)
  om_transferencias    → IPC log (comunicacion entre apps)
  om_pizarra_snapshot  → Backups (snapshots por ciclo)
"""
