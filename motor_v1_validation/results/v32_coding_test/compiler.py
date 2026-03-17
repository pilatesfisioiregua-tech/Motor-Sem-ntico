import json
import unittest
from typing import List, Dict, Any

# Definición de categorías e inteligencias irreducibles
CATEGORIAS = {
    "cuantitativa": ["INT-01", "INT-02", "INT-07"],
    "sistemica": ["INT-03", "INT-04"],
    "posicional": ["INT-05", "INT-06"],
    "interpretativa": ["INT-08", "INT-09", "INT-12"],
    "corporal": ["INT-10", "INT-15"],
    "expansiva": ["INT-13", "INT-14"],
    "operativa": ["INT-16"],
    "contemplativa": ["INT-17", "INT-18"]
}

INTELIGENCIAS_IRREDUCIBLES = ["INT-01", "INT-02", "INT-06", "INT-08", "INT-14", "INT-16"]
INTELIGENCIAS_FORMALES = CATEGORIAS["cuantitativa"] + CATEGORIAS["sistemica"]

def calcular_gaps(celdas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calcula el gap para cada celda (grado_objetivo - grado_actual) y añade el campo 'gap'.
    """
    for celda in celdas:
        celda['gap'] = celda['grado_objetivo'] - celda['grado_actual']
    return celdas

def ordenar_por_gap_desc(celdas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordena las celdas por gap descendente.
    """
    return sorted(celdas, key=lambda x: x['gap'], reverse=True)

def agrupar_por_inteligencia(celdas: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Agrupa celdas por inteligencia y calcula el gap promedio y total.
    """
    grupos = {}
    for celda in celdas:
        intel = celda['inteligencia']
        if intel not in grupos:
            grupos[intel] = {
                'inteligencia': intel,
                'gaps': [],
                'grados_actuales': [],
                'grados_objetivo': [],
                'celdas': []
            }
        grupos[intel]['gaps'].append(celda['gap'])
        grupos[intel]['grados_actuales'].append(celda['grado_actual'])
        grupos[intel]['grados_objetivo'].append(celda['grado_objetivo'])
        grupos[intel]['celdas'].append(celda)
    
    for intel, data in grupos.items():
        data['gap_promedio'] = sum(data['gaps']) / len(data['gaps'])
        data['gap_total'] = sum(data['gaps'])
        data['cantidad_celdas'] = len(data['celdas'])
    
    return grupos

def obtener_categoria(inteligencia: str) -> str:
    """
    Devuelve la categoría de una inteligencia.
    """
    for cat, intels in CATEGORIAS.items():
        if inteligencia in intels:
            return cat
    return "desconocida"

def seleccionar_inteligencias(grupos: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Aplica las reglas de selección para elegir 4-5 inteligencias.
    """
    # Ordenar inteligencias por gap promedio descendente
    inteligencias_ordenadas = sorted(grupos.keys(), key=lambda x: grupos[x]['gap_promedio'], reverse=True)
    
    seleccionadas = []
    
    # Regla 1: Núcleo irreducible (1 cuantitativa + 1 humana + INT-16)
    # 1.1 Seleccionar una cuantitativa con mayor gap
    cuantitativas = [i for i in inteligencias_ordenadas if obtener_categoria(i) == "cuantitativa"]
    if cuantitativas:
        seleccionadas.append(cuantitativas[0])
    
    # 1.2 Seleccionar una humana (no cuantitativa, no operativa) con mayor gap
    humanas = [i for i in inteligencias_ordenadas 
               if obtener_categoria(i) not in ["cuantitativa", "operativa"] and i not in seleccionadas]
    if humanas:
        seleccionadas.append(humanas[0])
    
    # 1.3 Seleccionar INT-16 si no está
    if "INT-16" in inteligencias_ordenadas and "INT-16" not in seleccionadas:
        seleccionadas.append("INT-16")
    
    # Regla 2: Máximo diferencial entre categorías (seleccionar de categorías no cubiertas)
    categorias_cubiertas = {obtener_categoria(i) for i in seleccionadas}
    
    # Completar hasta 4-5 inteligencias, priorizando categorías no cubiertas
    for inteligencia in inteligencias_ordenadas:
        if len(seleccionadas) >= 5:
            break
        if inteligencia in seleccionadas:
            continue
        cat = obtener_categoria(inteligencia)
        if cat not in categorias_cubiertas:
            seleccionadas.append(inteligencia)
            categorias_cubiertas.add(cat)
    
    # Si aún no tenemos 4, añadir las de mayor gap sin importar categoría
    for inteligencia in inteligencias_ordenadas:
        if len(seleccionadas) >= 5:
            break
        if inteligencia not in seleccionadas:
            seleccionadas.append(inteligencia)
    
    # Regla 3: Sweet spot 4-5 inteligencias (asegurar al menos 4)
    if len(seleccionadas) < 4:
        # Añadir las siguientes inteligencias con mayor gap
        for inteligencia in inteligencias_ordenadas:
            if inteligencia not in seleccionadas:
                seleccionadas.append(inteligencia)
                if len(seleccionadas) >= 4:
                    break
    
    return seleccionadas

def ordenar_configuracion(seleccionadas: List[str], grupos: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Aplica las reglas de orden para la configuración propuesta.
    """
    # Orden inicial por gap promedio descendente dentro de las seleccionadas
    orden_gap = sorted(seleccionadas, key=lambda x: grupos[x]['gap_promedio'], reverse=True)
    
    # Regla 11: Marco binario universal → INT-14+INT-01 primero (si ambos están presentes)
    if "INT-14" in orden_gap and "INT-01" in orden_gap:
        orden_gap.remove("INT-14")
        orden_gap.remove("INT-01")
        orden_gap = ["INT-14", "INT-01"] + orden_gap
    
    # Regla 4: Formales primero (cuantitativas y sistémicas)
    formales = [i for i in orden_gap if i in INTELIGENCIAS_FORMALES]
    no_formales = [i for i in orden_gap if i not in INTELIGENCIAS_FORMALES]
    
    # Mantener el orden relativo dentro de formales y no formales (Regla 5: No reorganizar secuencia)
    # El orden relativo ya está dado por orden_gap, que está ordenado por gap.
    # Al separar en formales y no formales, mantenemos el orden en que aparecían en orden_gap.
    configuracion = formales + no_formales
    
    return configuracion

def procesar_matriz(json_input: str) -> Dict[str, Any]:
    """
    Función principal que procesa el JSON de entrada y devuelve el resultado.
    """
    datos = json.loads(json_input)
    celdas = datos.get("celdas", [])
    
    # 1. Calcular gaps
    celdas_con_gap = calcular_gaps(celdas)
    
    # 2. Ordenar por gap descendente
    celdas_priorizadas = ordenar_por_gap_desc(celdas_con_gap)
    
    # 3. Agrupar por inteligencia
    grupos = agrupar_por_inteligencia(celdas_priorizadas)
    
    # 4. Seleccionar inteligencias (4-5)
    inteligencias_seleccionadas = seleccionar_inteligencias(grupos)
    
    # 5. Ordenar configuración propuesta
    configuracion_propuesta = ordenar_configuracion(inteligencias_seleccionadas, grupos)
    
    return {
        "celdas_priorizadas": celdas_priorizadas,
        "inteligencias_seleccionadas": inteligencias_seleccionadas,
        "configuracion_propuesta": configuracion_propuesta
    }

# ===========================================
# Tests unitarios
# ===========================================
class TestProcesarMatriz(unittest.TestCase):
    def setUp(self):
        # Datos de ejemplo con 21 celdas (3L×7F)
        self.celdas_ejemplo = []
        inteligencias = [
            "INT-01", "INT-02", "INT-03", "INT-04", "INT-05", "INT-06", "INT-07",
            "INT-08", "INT-09", "INT-10", "INT-12", "INT-13", "INT-14", "INT-15",
            "INT-16", "INT-17", "INT-18", "INT-01", "INT-02", "INT-03", "INT-04"
        ]
        for i, inteligencia in enumerate(inteligencias):
            self.celdas_ejemplo.append({
                "id": i + 1,
                "inteligencia": inteligencia,
                "grado_actual": i % 5,
                "grado_objetivo": (i % 5) + 2
            })
        self.json_input = json.dumps({"celdas": self.celdas_ejemplo})
    
    def test_gaps_calculados_correctamente(self):
        """Test 1: gaps se calculan correctamente"""
        resultado = procesar_matriz(self.json_input)
        celdas_priorizadas = resultado["celdas_priorizadas"]
        for celda in celdas_priorizadas:
            gap_esperado = celda["grado_objetivo"] - celda["grado_actual"]
            self.assertEqual(celda["gap"], gap_esperado)
    
    def test_regla_nucleo_irreducible(self):
        """Test 2: regla 1 se cumple (1 cuantitativa + 1 humana + INT-16)"""
        resultado = procesar_matriz(self.json_input)
        seleccionadas = resultado["inteligencias_seleccionadas"]
        
        # Verificar al menos una cuantitativa
        cuantitativas = [i for i in seleccionadas if obtener_categoria(i) == "cuantitativa"]
        self.assertGreaterEqual(len(cuantitativas), 1)
        
        # Verificar al menos una humana (no cuantitativa, no operativa)
        humanas = [i for i in seleccionadas if obtener_categoria(i) not in ["cuantitativa", "operativa"]]
        self.assertGreaterEqual(len(humanas), 1)
        
        # Verificar INT-16
        self.assertIn("INT-16", seleccionadas)
    
    def test_sweet_spot_4_5_inteligencias(self):
        """Test 3: regla 3 se cumple (4-5 inteligencias seleccionadas)"""
        resultado = procesar_matriz(self.json_input)
        seleccionadas = resultado["inteligencias_seleccionadas"]
        self.assertTrue(4 <= len(seleccionadas) <= 5)
    
    def test_formal_primero_en_orden(self):
        """Test 4: regla 4 se cumple (formal primero en el orden)"""
        resultado = procesar_matriz(self.json_input)
        configuracion = resultado["configuracion_propuesta"]
        
        # Encontrar el índice de la primera no formal
        indices_formales = [i for i, intel in enumerate(configuracion) if intel in INTELIGENCIAS_FORMALES]
        indices_no_formales = [i for i, intel in enumerate(configuracion) if intel not in INTELIGENCIAS_FORMALES]
        
        if indices_formales and indices_no_formales:
            # Todos los formales deben estar antes que cualquier no formal
            self.assertLess(max(indices_formales), min(indices_no_formales))
    
    def test_marco_binario_int14_int01_primero(self):
        """Test 5: regla 11 se cumple (marco binario → INT-14+INT-01 primero si aplica)"""
        # Modificar datos para asegurar que INT-14 e INT-01 están seleccionados
        celdas_mod = self.celdas_ejemplo.copy()
        # Aumentar gaps de INT-14 e INT-01 para que sean seleccionados
        for celda in celdas_mod:
            if celda["inteligencia"] in ["INT-14", "INT-01"]:
                celda["grado_objetivo"] = 10
        json_mod = json.dumps({"celdas": celdas_mod})
        
        resultado = procesar_matriz(json_mod)
        configuracion = resultado["configuracion_propuesta"]
        
        # Si ambos están en la configuración, deben ser los dos primeros en ese orden
        if "INT-14" in configuracion and "INT-01" in configuracion:
            self.assertEqual(configuracion[0], "INT-14")
            self.assertEqual(configuracion[1], "INT-01")

if __name__ == "__main__":
    # Ejecutar tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProcesarMatriz)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
