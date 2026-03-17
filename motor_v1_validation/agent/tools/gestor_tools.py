"""Gestor tools — analizar_gradientes, compilar_programa."""

import json


def register_tools(registry, sandbox_dir=""):
    registry.register("analizar_gradientes", {
        "name": "analizar_gradientes",
        "description": "Analiza un caso y calcula su campo de gradientes (que celdas de la Matriz 3Lx7F tienen gap). Usa esto cuando el usuario presenta un caso o situacion para analizar.",
        "parameters": {"type": "object", "properties": {
            "input": {"type": "string", "description": "El caso o situacion a analizar"},
        }, "required": ["input"]}
    }, lambda a: _tool_gradientes(a["input"]), category="gestor")

    registry.register("compilar_programa", {
        "name": "compilar_programa",
        "description": "Compila un programa de preguntas optimo para un caso. Selecciona inteligencias, preguntas y modelos basandose en los gradientes y la efectividad acumulada.",
        "parameters": {"type": "object", "properties": {
            "input": {"type": "string", "description": "El caso a analizar"},
            "consumidor": {"type": "string", "description": "ID del consumidor (motor_vn, exocortex:pilates, exocortex:fisioterapia)"},
        }, "required": ["input"]}
    }, lambda a: _tool_compilar(a["input"], a.get("consumidor", "motor_vn")), category="gestor")


def _tool_gradientes(input_texto):
    from core.gestor import calcular_gradientes
    result = calcular_gradientes(input_texto)
    return json.dumps(result, indent=2, default=str)


def _tool_compilar(input_texto, consumidor):
    from core.gestor import calcular_gradientes, compilar_programa
    gradientes = calcular_gradientes(input_texto)
    programa = compilar_programa(gradientes, consumidor)
    return json.dumps({"gradientes": gradientes, "programa": programa}, indent=2, default=str)
