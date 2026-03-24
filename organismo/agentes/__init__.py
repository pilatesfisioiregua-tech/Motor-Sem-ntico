"""Agentes Autónomos — Patrón PULL desde pizarra.

Cada agente es un NodoVivo que:
1. Lee receta de pizarra cognitiva (P63)
2. Ejecuta sensor SQL
3. Construye prompt D_híbrido
4. Llama motor.pensar() (Sandwich LLM)
5. Verifica con kernel.verificar() ($0)
6. Emite señales al bus
"""
