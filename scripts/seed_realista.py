"""Seed realista para Authentic Pilates.

Crea: 20 clientes + contratos + 8 semanas de sesiones/asistencias + cargos + pagos.
Ejecutar una vez: python scripts/seed_realista.py

Idempotente: verifica si ya hay datos antes de insertar.
"""
import asyncio
import json
import random
import sys
from datetime import date, timedelta, time
from pathlib import Path
from uuid import UUID

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

TENANT = "authentic_pilates"

# 20 clientes ficticios (nombres comunes España)
CLIENTES = [
    {"nombre": "María", "apellidos": "García López", "telefono": "600111001", "email": "maria.garcia@email.com"},
    {"nombre": "Ana", "apellidos": "Martínez Ruiz", "telefono": "600111002", "email": "ana.martinez@email.com"},
    {"nombre": "Carmen", "apellidos": "Fernández Gil", "telefono": "600111003", "email": None},
    {"nombre": "Laura", "apellidos": "Sánchez Díaz", "telefono": "600111004", "email": "laura.sanchez@email.com"},
    {"nombre": "Elena", "apellidos": "Pérez Moreno", "telefono": "600111005", "email": None},
    {"nombre": "Isabel", "apellidos": "Gómez Torres", "telefono": "600111006", "email": "isabel.gomez@email.com"},
    {"nombre": "Lucía", "apellidos": "Romero Vega", "telefono": "600111007", "email": None},
    {"nombre": "Pilar", "apellidos": "Hernández Soto", "telefono": "600111008", "email": "pilar.hernandez@email.com"},
    {"nombre": "Rosa", "apellidos": "Alonso Prieto", "telefono": "600111009", "email": None},
    {"nombre": "Marta", "apellidos": "Navarro Blanco", "telefono": "600111010", "email": "marta.navarro@email.com"},
    {"nombre": "Sara", "apellidos": "Jiménez Castro", "telefono": "600111011", "email": None},
    {"nombre": "Cristina", "apellidos": "Díaz Herrero", "telefono": "600111012", "email": "cristina.diaz@email.com"},
    {"nombre": "Patricia", "apellidos": "Muñoz Ramos", "telefono": "600111013", "email": None},
    {"nombre": "Teresa", "apellidos": "Álvarez Rubio", "telefono": "600111014", "email": "teresa.alvarez@email.com"},
    {"nombre": "Raquel", "apellidos": "Molina Ortega", "telefono": "600111015", "email": None},
    {"nombre": "Sandra", "apellidos": "Morales Ibáñez", "telefono": "600111016", "email": "sandra.morales@email.com"},
    {"nombre": "Beatriz", "apellidos": "Suárez Delgado", "telefono": "600111017", "email": None},
    {"nombre": "Paula", "apellidos": "Vidal Crespo", "telefono": "600111018", "email": "paula.vidal@email.com"},
    # 2 individuales
    {"nombre": "Carlos", "apellidos": "Ruiz Medina", "telefono": "600111019", "email": "carlos.ruiz@email.com", "individual": True, "freq": 2},
    {"nombre": "Javier", "apellidos": "López Serrano", "telefono": "600111020", "email": None, "individual": True, "freq": 1},
]


async def seed():
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Verificar si ya hay datos
        existing = await conn.fetchval(
            "SELECT count(*) FROM om_clientes WHERE telefono LIKE '600111%'")
        if existing >= 15:
            print(f"Ya hay {existing} clientes seed. Saltando.")
            return

        # Obtener grupos
        grupos = await conn.fetch("""
            SELECT id, nombre, capacidad_max, dias_semana, precio_mensual
            FROM om_grupos WHERE tenant_id = $1 AND estado = 'activo'
            ORDER BY nombre
        """, TENANT)
        if not grupos:
            print("ERROR: No hay grupos. Ejecutar B-PIL-02 primero.")
            return

        grupo_ids = [g["id"] for g in grupos]
        cliente_ids = []
        contrato_ids = []

        # ============ CREAR CLIENTES + CONTRATOS ============
        print("Creando 20 clientes...")
        grupo_idx = 0
        for c in CLIENTES:
            # Crear cliente
            row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    consentimiento_datos, fecha_consentimiento,
                    metodo_pago_habitual, metodo_pago_confianza)
                VALUES ($1,$2,$3,$4, true, now(), $5, 0.8)
                RETURNING id
            """, c["nombre"], c["apellidos"], c["telefono"], c.get("email"),
                random.choice(["bizum", "efectivo", "tpv"]))
            cid = row["id"]
            cliente_ids.append(cid)

            # Relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado, fuente_captacion)
                VALUES ($1, $2, 'activo', $3)
            """, cid, TENANT, random.choice(["recomendacion", "instagram", "web", "pasaba_por_aqui"]))

            # Contrato
            if c.get("individual"):
                freq = c["freq"]
                precio = 30.0 if freq >= 2 else 35.0
                co_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                        frecuencia_semanal, precio_sesion, ciclo_cobro, fecha_inicio)
                    VALUES ($1,$2,'individual',$3,$4,'sesion',$5) RETURNING id
                """, TENANT, cid, freq, precio, date.today() - timedelta(days=60))
            else:
                # Asignar a grupo (round-robin, max capacidad)
                grupo = grupos[grupo_idx % len(grupos)]
                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id=$1 AND estado='activo'
                """, grupo["id"])
                while ocupados >= grupo["capacidad_max"]:
                    grupo_idx += 1
                    grupo = grupos[grupo_idx % len(grupos)]
                    ocupados = await conn.fetchval("""
                        SELECT count(*) FROM om_contratos
                        WHERE grupo_id=$1 AND estado='activo'
                    """, grupo["id"])

                co_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                        grupo_id, precio_mensual, fecha_inicio)
                    VALUES ($1,$2,'grupo',$3,$4,$5) RETURNING id
                """, TENANT, cid, grupo["id"], grupo["precio_mensual"],
                    date.today() - timedelta(days=60))
                grupo_idx += 1

            contrato_ids.append(co_row["id"])
            print(f"  {c['nombre']} {c['apellidos']} → {'individual' if c.get('individual') else grupo['nombre']}")

        # ============ CREAR SESIONES + ASISTENCIAS (8 semanas) ============
        print("\nGenerando 8 semanas de sesiones...")
        hoy = date.today()
        lunes_inicio = hoy - timedelta(days=hoy.weekday()) - timedelta(weeks=8)
        total_sesiones = 0
        total_asistencias = 0

        for semana in range(9):  # 8 pasadas + actual
            lunes = lunes_inicio + timedelta(weeks=semana)

            for grupo in grupos:
                dias = grupo["dias_semana"]
                if isinstance(dias, str):
                    dias = json.loads(dias)

                for slot in dias:
                    fecha_sesion = lunes + timedelta(days=slot["dia"] - 1)
                    if fecha_sesion > hoy:
                        continue  # No crear sesiones futuras

                    # Verificar si ya existe
                    exists = await conn.fetchval("""
                        SELECT 1 FROM om_sesiones
                        WHERE grupo_id=$1 AND fecha=$2 AND tenant_id=$3
                    """, grupo["id"], fecha_sesion, TENANT)
                    if exists:
                        continue

                    hi = time.fromisoformat(slot["hi"])
                    hf = time.fromisoformat(slot["hf"])

                    ses_row = await conn.fetchrow("""
                        INSERT INTO om_sesiones (tenant_id, tipo, grupo_id, instructor,
                            fecha, hora_inicio, hora_fin, estado)
                        VALUES ($1,'grupo',$2,'Jesus',$3,$4,$5,'completada') RETURNING id
                    """, TENANT, grupo["id"], fecha_sesion, hi, hf)
                    total_sesiones += 1

                    # Asistencias para miembros del grupo
                    miembros = await conn.fetch("""
                        SELECT co.id as contrato_id, co.cliente_id
                        FROM om_contratos co
                        WHERE co.grupo_id=$1 AND co.estado='activo'
                    """, grupo["id"])

                    for m in miembros:
                        # 85% asistencia, 10% no_vino, 5% cancelada
                        r = random.random()
                        if r < 0.85:
                            estado = "asistio"
                        elif r < 0.95:
                            estado = "no_vino"
                        else:
                            estado = "cancelada"

                        await conn.execute("""
                            INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id,
                                contrato_id, estado)
                            VALUES ($1,$2,$3,$4,$5)
                        """, TENANT, ses_row["id"], m["cliente_id"], m["contrato_id"], estado)
                        total_asistencias += 1

        print(f"  {total_sesiones} sesiones, {total_asistencias} asistencias")

        # ============ CREAR CARGOS (suscripciones 2 meses) ============
        print("\nGenerando cargos de suscripción...")
        total_cargos = 0
        for mes_offset in [2, 1]:  # Hace 2 meses y hace 1 mes
            mes = (hoy.replace(day=1) - timedelta(days=mes_offset * 28)).replace(day=1)
            contratos_grupo = await conn.fetch("""
                SELECT co.id, co.cliente_id, COALESCE(co.precio_mensual, g.precio_mensual) as precio
                FROM om_contratos co
                JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id=$1 AND co.tipo='grupo' AND co.estado='activo'
            """, TENANT)

            for co in contratos_grupo:
                exists = await conn.fetchval("""
                    SELECT 1 FROM om_cargos
                    WHERE contrato_id=$1 AND tipo='suscripcion_grupo' AND periodo_mes=$2
                """, co["id"], mes)
                if exists:
                    continue
                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id, tipo,
                        descripcion, base_imponible, periodo_mes, estado, fecha_cargo, fecha_cobro)
                    VALUES ($1,$2,$3,'suscripcion_grupo',$4,$5,$6,'cobrado',$7,$7)
                """, TENANT, co["cliente_id"], co["id"],
                    f"Suscripción {mes.strftime('%B %Y')}",
                    float(co["precio"]), mes, mes + timedelta(days=5))
                total_cargos += 1

        print(f"  {total_cargos} cargos de suscripción")

        # ============ CREAR PAGOS (conciliar cargos) ============
        print("\nGenerando pagos...")
        cargos_cobrados = await conn.fetch("""
            SELECT id, cliente_id, total, fecha_cobro FROM om_cargos
            WHERE tenant_id=$1 AND estado='cobrado' AND total IS NOT NULL
        """, TENANT)

        pagos_creados = 0
        for cargo in cargos_cobrados:
            metodo = random.choice(["bizum", "efectivo", "tpv", "transferencia"])
            pago_row = await conn.fetchrow("""
                INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto, fecha_pago)
                VALUES ($1,$2,$3,$4,$5) RETURNING id
            """, TENANT, cargo["cliente_id"], metodo,
                float(cargo["total"]), cargo["fecha_cobro"] or date.today())

            await conn.execute("""
                INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado)
                VALUES ($1,$2,$3)
            """, pago_row["id"], cargo["id"], float(cargo["total"]))
            pagos_creados += 1

        print(f"  {pagos_creados} pagos registrados")

        # ============ ADN SEMILLA ============
        print("\nCreando ADN semilla...")
        adn_items = [
            ("principio_innegociable", "Grupos máximo 4 personas", "Pilates reformer requiere atención individualizada. Nunca más de 4 en reformer."),
            ("filosofia", "El cuerpo habla primero", "Antes de corregir verbalmente, observar. El cuerpo del alumno dice lo que necesita antes de que pregunte."),
            ("metodo", "EEDAP", "Evaluar-Explicar-Demostrar-Asistir-Practicar. Secuencia de enseñanza para cada ejercicio nuevo."),
            ("antipatron", "No competir en precio", "Authentic Pilates compite en calidad y atención, nunca en precio. Si alguien busca barato, no es nuestro cliente."),
            ("criterio_depuracion", "Si no aporta al alumno, eliminar", "Cada ejercicio, cada proceso, cada gasto debe pasar el test: ¿mejora la experiencia del alumno?"),
        ]
        for cat, titulo, desc in adn_items:
            exists = await conn.fetchval(
                "SELECT 1 FROM om_adn WHERE tenant_id=$1 AND titulo=$2", TENANT, titulo)
            if not exists:
                await conn.execute("""
                    INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion, funcion_l07)
                    VALUES ($1,$2,$3,$4,'F5')
                """, TENANT, cat, titulo, desc)
        print(f"  {len(adn_items)} principios ADN")

        # ============ GASTOS SEMILLA ============
        print("\nCreando gastos fijos...")
        gastos = [
            ("alquiler", "Alquiler local", 800, True, "mensual"),
            ("seguros", "Seguro RC profesional", 45, True, "mensual"),
            ("suministros", "Luz + agua", 120, True, "mensual"),
            ("limpieza", "Servicio limpieza", 150, True, "mensual"),
            ("gestor", "Gestoría", 80, True, "mensual"),
            ("software", "Dominio + hosting", 15, True, "mensual"),
        ]
        for cat, desc, importe, recurrente, periodo in gastos:
            for mes_offset in [2, 1, 0]:
                fecha = (hoy.replace(day=1) - timedelta(days=mes_offset * 28)).replace(day=1)
                exists = await conn.fetchval("""
                    SELECT 1 FROM om_gastos WHERE tenant_id=$1 AND categoria=$2 AND fecha_gasto=$3
                """, TENANT, cat, fecha)
                if exists:
                    continue
                iva = round(importe * 0.21, 2)
                await conn.execute("""
                    INSERT INTO om_gastos (tenant_id, categoria, descripcion,
                        base_imponible, iva_porcentaje, iva_soportado, total,
                        es_recurrente, periodicidad, fecha_gasto, fecha_pago)
                    VALUES ($1,$2,$3,$4,21.00,$5,$6,$7,$8,$9,$9)
                """, TENANT, cat, desc, importe, iva, round(importe + iva, 2),
                    recurrente, periodo, fecha)
        print(f"  {len(gastos)} gastos × 3 meses")

    print("\n✅ Seed realista completado.")


if __name__ == "__main__":
    asyncio.run(seed())
