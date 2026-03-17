"""Reporter — traduce resultados tecnicos a lenguaje de negocio. $0, sin LLM."""


# Templates OMNI-MIND
TEMPLATE_COSTE = (
    "Este mes llevas ${gastado:.2f} de ${limite:.2f} ({pct:.0f}%). "
    "{modelo_mas_caro} es el que mas consume ({pct_modelo:.0f}%). "
    "{proyeccion}"
)

TEMPLATE_ESTADO = (
    "El sistema tiene {preguntas} preguntas, {datapoints} datapoints, "
    "{modelos} modelos activos. {alertas_texto}. {autopoiesis_texto}."
)

TEMPLATE_ERROR = (
    "Hay {n_señales} alertas pendientes. "
    "La mas grave: {peor_señal}. {recomendacion}."
)

TEMPLATE_DATOS = (
    "Los pilotos ({nombres_pilotos}) tienen {n_datapoints} datos cada uno. "
    "{estado_conexion}. {recomendacion}."
)

TEMPLATE_RENDIMIENTO = (
    "Latencia media: {latencia}ms. SLOs: {slo_status}. {cuello_botella}."
)


class Reporter:
    """Generates human-readable reports from technical data."""

    def summarize_session(self, result: dict) -> str:
        """Summarize an agent session result in plain Spanish."""
        stop = result.get("stop_reason", "unknown")
        iters = result.get("iterations", 0)
        cost = result.get("cost_usd", 0)
        files = result.get("files_changed", [])
        output = result.get("result", "")

        if stop == "DONE":
            parts = [f"Completado en {iters} pasos"]
            if files:
                parts.append(f"modifique {len(files)} archivo(s)")
            if output:
                summary = output[:200].replace('\n', ' ')
                parts.append(f"resultado: {summary}")
            msg = ", ".join(parts) + "."
        elif "TIMEOUT" in str(stop):
            msg = f"Se agoto el tiempo tras {iters} pasos. La tarea quedo incompleta."
        elif "DRIFT" in str(stop):
            msg = f"Me desvie del tema y pare para no hacer cambios incorrectos."
        elif "BUDGET" in str(stop):
            msg = f"Se agoto el presupuesto (${cost:.2f}) tras {iters} pasos."
        else:
            msg = f"No pude completar la tarea tras {iters} pasos. Razon: {stop}."

        if cost > 0:
            msg += f" Coste: ${cost:.4f}."

        return msg

    def summarize_diagnostics(self, diagnostics: dict) -> str:
        """Translate technical diagnostics to business language."""
        category = diagnostics.get("category", "")

        if category == "coste":
            gastado = diagnostics.get("gastado", 0)
            limite = diagnostics.get("limite", 200)
            pct = (gastado / limite * 100) if limite > 0 else 0
            modelo = diagnostics.get("modelo_mas_caro", "desconocido")
            pct_modelo = diagnostics.get("pct_modelo", 0)

            if pct > 100:
                proyeccion = "Has superado el presupuesto."
            elif pct > 80:
                proyeccion = f"Ojo: vas al {pct:.0f}%, queda poco margen."
            else:
                proyeccion = f"Vas bien, queda ${limite - gastado:.2f} disponible."

            return TEMPLATE_COSTE.format(
                gastado=gastado, limite=limite, pct=pct,
                modelo_mas_caro=modelo, pct_modelo=pct_modelo,
                proyeccion=proyeccion,
            )

        elif category == "estado":
            return TEMPLATE_ESTADO.format(
                preguntas=diagnostics.get("preguntas", 0),
                datapoints=diagnostics.get("datapoints", 0),
                modelos=diagnostics.get("modelos", 0),
                alertas_texto=self._alertas_texto(diagnostics.get("alertas", 0)),
                autopoiesis_texto=self._autopoiesis_texto(diagnostics.get("ciclo_roto", False)),
            )

        elif category == "error":
            return TEMPLATE_ERROR.format(
                n_señales=diagnostics.get("n_señales", 0),
                peor_señal=diagnostics.get("peor_señal", "ninguna"),
                recomendacion=diagnostics.get("recomendacion", "Revisar manualmente"),
            )

        elif category == "datos":
            return TEMPLATE_DATOS.format(
                nombres_pilotos=diagnostics.get("nombres_pilotos", "sin datos"),
                n_datapoints=diagnostics.get("n_datapoints", 0),
                estado_conexion=diagnostics.get("estado_conexion", "sin informacion"),
                recomendacion=diagnostics.get("recomendacion", "Verificar configuracion"),
            )

        elif category == "rendimiento":
            return TEMPLATE_RENDIMIENTO.format(
                latencia=diagnostics.get("latencia", 0),
                slo_status=diagnostics.get("slo_status", "sin datos"),
                cuello_botella=diagnostics.get("cuello_botella", "sin detectar"),
            )

        # Generic fallback
        return f"Diagnostico ({category}): {diagnostics}"

    def answer_question(self, question: str, data: dict) -> str:
        """Answer a business question using technical data."""
        q_lower = question.lower()

        if any(kw in q_lower for kw in ["cuánto", "cuanto", "gasto", "gastado", "coste"]):
            gastado = data.get("gastado", data.get("coste_total", 0))
            limite = data.get("limite", data.get("limite_mensual", 200))
            modelo_top = data.get("modelo_top", data.get("modelo_mas_caro", ""))
            pct_modelo = data.get("pct_modelo", 0)
            proyeccion = data.get("proyeccion", gastado * 2)

            msg = f"Este mes llevas ${gastado:.2f}."
            if modelo_top:
                msg += f" El {pct_modelo:.0f}% es de {modelo_top}."
            if proyeccion:
                msg += f" Proyeccion a fin de mes: ${proyeccion:.2f}."
            if limite:
                restante = limite - gastado
                msg += f" Te quedan ${restante:.2f} de presupuesto."
            return msg

        elif any(kw in q_lower for kw in ["lento", "rápido", "rapido", "latencia", "velocidad"]):
            latencia = data.get("latencia", data.get("latencia_media", 0))
            normal = data.get("latencia_normal", 3000)
            msg = f"El sistema responde en {latencia}ms"
            if latencia > normal:
                msg += f" (lo normal es {normal}ms, va lento)."
            else:
                msg += f" (dentro de lo normal)."
            return msg

        elif any(kw in q_lower for kw in ["error", "falla", "roto", "problema"]):
            n = data.get("n_errores", data.get("n_señales", 0))
            peor = data.get("peor_señal", data.get("error_principal", "ninguno"))
            if n == 0:
                return "No hay errores activos. Todo funciona correctamente."
            return f"Hay {n} problemas sin resolver. El mas grave: {peor}."

        elif any(kw in q_lower for kw in ["estado", "cómo está", "como esta", "salud"]):
            ok = data.get("sistema_ok", True)
            alertas = data.get("alertas", 0)
            if ok and alertas == 0:
                return "El sistema esta funcionando correctamente, sin alertas."
            elif ok:
                return f"Funciona pero hay {alertas} alerta(s) pendiente(s)."
            else:
                return f"Hay problemas: {data.get('resumen_problemas', 'revisar diagnostico')}."

        # Fallback
        return f"Datos disponibles: {', '.join(f'{k}={v}' for k, v in list(data.items())[:5])}"

    def _alertas_texto(self, n: int) -> str:
        if n == 0:
            return "Sin alertas pendientes"
        elif n == 1:
            return "1 alerta pendiente"
        return f"{n} alertas pendientes"

    def _autopoiesis_texto(self, roto: bool) -> str:
        if roto:
            return "Ciclo autopoietico roto (el sistema no se auto-mantiene)"
        return "Ciclo autopoietico OK"
