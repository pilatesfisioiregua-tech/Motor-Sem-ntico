# ACTUALIZACIÓN DOCUMENTO MAESTRO — Principio 32: Enjambre como Red Neuronal

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-13
**Origen:** Sesión diseño Chief OS Chat + estigmergia validada empíricamente

---

## Añadir a §12 PRINCIPIOS DE DISEÑO

**32. El enjambre no es un pipeline — es una red neuronal cuyos nodos son LLMs.** La Matriz 3L×7F no es un mapa de inteligencias — es la **matriz de pesos** de la red. El Gestor la entrena. Los modelos son fungibles. La topología es el producto.

---

## Añadir a §1 QUÉ ES (párrafo adicional) o crear §1E: EL ENJAMBRE COMO RED NEURONAL

### Fundamento

Una red neuronal clásica: nodos simples (funciones de activación), conexiones con pesos, aprendizaje por backpropagation. El enjambre OMNI-MIND: nodos masivos (LLMs de 100B+ params), conexiones con pesos derivados de la Matriz, aprendizaje por datos de efectividad (gap_cerrado por modelo×celda×pregunta).

La diferencia no es metafórica — es estructural:

| Propiedad | Red neuronal clásica | Enjambre OMNI-MIND |
|-----------|---------------------|-------------------|
| Nodo | función de activación (ReLU, sigmoid) | LLM completo (V3.2, R1, Cogito) |
| Peso de conexión | float aprendido por backprop | tasa_media_cierre de modelo→celda (datos Gestor) |
| Capa oculta | representación intermedia | ronda de estigmergia (output parcial que alimenta la siguiente ronda) |
| Forward pass | input → capas → output (ms) | pregunta → rondas de enjambre → síntesis (segundos) |
| Backpropagation | gradiente del error | feedback de efectividad: ¿la respuesta cerró el gap? |
| Topología | fija por arquitectura | dinámica por input — la Matriz decide qué conexiones se activan |

### 6 implicaciones arquitecturales

**1. No se diseña el enjambre — se entrena.**
La asignación modelo→celda emerge de datos de efectividad, no de decisión humana. Los datos de Exp 4 lo confirman: GPT-OSS es motor en pizarra (119 contribuciones) pero esponja en evaluación (0 aportes únicos). El mismo nodo cambia de peso según el mecanismo. El Gestor acumula estos datos y recalcula pesos continuamente.

**2. La topología es dinámica por input.**
No todos los nodos se activan para cada pregunta. El campo de gradientes de la Matriz determina qué celdas tienen gap, y eso determina qué modelos (nodos) y qué conexiones se activan. Una pregunta financiera activa una sub-red; una pregunta de diseño activa otra. Mismos nodos disponibles, diferente cableado.

**3. Las rondas de estigmergia son capas ocultas.**
En la pizarra, ronda 1 = capa de entrada (cada nodo dispara independiente). Ronda 2 = capa oculta (cada nodo incorpora señales de los demás). Síntesis = capa de salida. Las capas ocultas producen representaciones emergentes: Exp 4.3 generó 425 conexiones y 239 puntos ciegos que ningún nodo individual habría producido. Eso es exactamente lo que hacen las capas ocultas de una red — crear features que no existen en los datos de entrada.

**4. Cada exocortex es una red con topología propia.**
El exocortex de pilates y el de la clínica no son copias con datos diferentes. Son redes con los mismos nodos disponibles pero diferente topología de conexiones, entrenada por los datos de efectividad de su dominio. El Gestor compila un "programa de pesos" diferente para cada consumidor.

**5. Scaling = topología, no volumen.**
Exp 4 lo demostró: 12 modelos producían valor concentrado en 2-3 nodos (Qwen como cerebro, GPT-OSS como motor). Los otros eran peso muerto. Añadir nodos sin ajustar la topología no mejora la red — añade ruido. La red óptima es pequeña y bien conectada.

**6. El moat es la red entrenada.**
Los modelos son públicos. Los providers son públicos. La infraestructura es commodity. Lo que no es público: miles de datapoints de efectividad que dicen "para este patrón de gaps, esta combinación de modelos con estos pesos produce el mejor cierre de gap". Esa es la propiedad intelectual del sistema.

### Consecuencia para el roadmap

El Gestor de la Matriz no es un componente más — es el **algoritmo de entrenamiento** de la red. Sin él, el enjambre hace forward pass con pesos fijos (hardcoded). Con él, cada ejecución ajusta la topología. Implementar el Gestor es la diferencia entre un pipeline estático y un sistema que aprende.

### Dato empírico de soporte

Sesión 2026-03-13: primera ejecución de enjambre con estigmergia (2 rondas + pizarra + síntesis). 3 modelos (V3.2-chat, V3.1, R1) + Cogito sintetizador. Ronda 2 muestra 3+ referencias cruzadas donde los modelos reaccionan al output de los otros. Coste: $0.009. La red feedforward básica funciona — los nodos producen más cuando están conectados que cuando operan aislados.

---

## Añadir a §0 CAMBIOS DE ESTA VERSIÓN

| Cambio | Origen | Sección |
|--------|--------|---------|
| **El enjambre es una red neuronal de LLMs. La Matriz = matriz de pesos. El Gestor = algoritmo de entrenamiento.** | Sesión 13-mar | §1E, §12 |
| **Estigmergia validada empíricamente: ronda 2 produce referencias cruzadas entre modelos** | Sesión 13-mar | §12 |
| **Principio 32: Los modelos son fungibles, la topología es el producto** | Sesión 13-mar | §12 |

---

*CR0 — Jesús valida y cierra*
