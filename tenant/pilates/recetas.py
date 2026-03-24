"""Recetas dominio Pilates — prescripciones especificas del sector.

Seeds de recetas que el organismo usa como base.
Se enriquecen con aprendizaje del circuito de gomas.
"""
from __future__ import annotations

RECETAS_PILATES = {
    # ============================================================
    # F1 CONSERVACION — Proteger lo que hay
    # ============================================================
    "F1_fantasma_llamada": {
        "funcion": "F1",
        "nombre": "Llamada personal cliente fantasma",
        "descripcion": "Llamar al cliente que lleva 3+ semanas sin venir. "
                       "No enviar WA genérico — llamar por teléfono, preguntar qué tal.",
        "accion": "llamar_telefono",
        "trigger": "dias_sin_asistir >= 21",
        "efectividad_base": 0.65,
        "coste_estimado_min": 5,
        "requiere_cr1": False,
    },
    "F1_racha_rota": {
        "funcion": "F1",
        "nombre": "Recuperar racha rota",
        "descripcion": "Cliente con racha >4 semanas que rompió. "
                       "WA personal: '¿todo bien? te echamos de menos el [día]'",
        "accion": "enviar_wa_personal",
        "trigger": "racha_rota AND racha_anterior >= 4",
        "efectividad_base": 0.55,
        "coste_estimado_min": 2,
        "requiere_cr1": False,
    },
    "F1_deuda_conversacion": {
        "funcion": "F1",
        "nombre": "Conversación sobre deuda pendiente",
        "descripcion": "Hablar en persona (no WA) con el cliente que debe >60€. "
                       "Ofrecer plan de pago si es necesario.",
        "accion": "conversacion_presencial",
        "trigger": "deuda > 60 AND dias_deuda > 14",
        "efectividad_base": 0.50,
        "coste_estimado_min": 10,
        "requiere_cr1": True,
    },

    # ============================================================
    # F2 CAPTACION — Atraer nuevos
    # ============================================================
    "F2_clase_prueba": {
        "funcion": "F2",
        "nombre": "Clase de prueba gratuita",
        "descripcion": "Ofrecer 1 clase gratis a contactos interesados. "
                       "Mejor resultado si es en grupo con plaza libre.",
        "accion": "programar_clase_prueba",
        "trigger": "contacto_nuevo OR referido",
        "efectividad_base": 0.40,
        "coste_estimado_min": 0,
        "requiere_cr1": False,
    },
    "F2_referidos": {
        "funcion": "F2",
        "nombre": "Programa referidos 15%",
        "descripcion": "Descuento 15% primer mes para referidos. "
                       "El que refiere también recibe descuento ese mes.",
        "accion": "activar_descuento_referido",
        "trigger": "manual OR contacto_derivado_fisio",
        "efectividad_base": 0.45,
        "coste_estimado_min": 0,
        "requiere_cr1": False,
    },

    # ============================================================
    # F3 DEPURACION — Eliminar lo que sobra
    # ============================================================
    "F3_cerrar_grupo_vacio": {
        "funcion": "F3",
        "nombre": "Cerrar grupo con 1 alumno",
        "descripcion": "Fusionar alumno a otro grupo compatible. "
                       "Libera franja horaria para Jesús.",
        "accion": "fusionar_grupo",
        "trigger": "inscritos <= 1 AND ingreso < coste_oportunidad",
        "efectividad_base": 0.80,
        "coste_estimado_min": 15,
        "requiere_cr1": True,
    },
    "F3_optimizar_horarios": {
        "funcion": "F3",
        "nombre": "Optimizar horarios por demanda",
        "descripcion": "Mover grupos de franjas muertas a franjas con lista de espera.",
        "accion": "reubicar_horario",
        "trigger": "ocupacion < 50% AND existe_franja_llena",
        "efectividad_base": 0.60,
        "coste_estimado_min": 30,
        "requiere_cr1": True,
    },

    # ============================================================
    # F4 ESTRATEGIA — Decidir rumbo
    # ============================================================
    "F4_subir_precio": {
        "funcion": "F4",
        "nombre": "Test subida precio grupo",
        "descripcion": "De 105€ a 120€/mes en grupos nuevos. "
                       "Clientes actuales mantienen precio 3 meses.",
        "accion": "ajustar_precio_nuevos",
        "trigger": "ocupacion > 80% AND churn < 5%",
        "efectividad_base": 0.70,
        "coste_estimado_min": 5,
        "requiere_cr1": True,
    },

    # ============================================================
    # F5 IDENTIDAD — Lo que nos hace unicos
    # ============================================================
    "F5_testimonio_video": {
        "funcion": "F5",
        "nombre": "Recoger testimonio en vídeo",
        "descripcion": "Pedir a 2-3 clientes satisfechos un vídeo breve "
                       "contando su experiencia. Para Instagram + web.",
        "accion": "solicitar_testimonio",
        "trigger": "asistencia > 90% AND meses > 6",
        "efectividad_base": 0.55,
        "coste_estimado_min": 10,
        "requiere_cr1": False,
    },

    # ============================================================
    # F7 REPLICACION — Que funcione sin Jesus
    # ============================================================
    "F7_manual_instructor": {
        "funcion": "F7",
        "nombre": "Crear manual operativo instructor",
        "descripcion": "Documentar: qué hacer cuando llega nuevo, "
                       "qué hacer ante lesión, cuándo cobrar, cuándo consultar a Jesús.",
        "accion": "generar_documento",
        "trigger": "manual_version IS NULL OR manual_version < '2.0'",
        "efectividad_base": 0.60,
        "coste_estimado_min": 60,
        "requiere_cr1": True,
    },
}
