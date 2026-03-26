from repositories.base_repo import prestamo_repo, config_repo, socio_repo
from core.exceptions import BusinessError
from bson import ObjectId
from datetime import datetime

class PrestamoService:
    @staticmethod
    def _calcular_plan_decreciente(monto_restante: float, tasa_mensual: float, cuotas_restantes: int, cuota_inicio: int, saldo_interes: float = None):
        """
        Genera el cronograma de pagos programado.
        Regla: Amortización programada de capital constante sobre monto_restante.
        El interés se calcula sobre saldo_interes (si se provee) o sobre saldo decreciente.
        """
        plan = []
        if cuotas_restantes <= 0: return []
        
        # Amortización programada base sobre el capital que falta repartir
        amort_base = round(monto_restante / cuotas_restantes, 2)
        
        # El saldo para amortización (lo que queda por repartir)
        saldo_repartir = round(monto_restante, 2)
        # El saldo para intereses (lo que realmente debe el socio)
        saldo_real = round(saldo_interes if saldo_interes is not None else monto_restante, 2)
        
        for i in range(cuota_inicio, cuota_inicio + cuotas_restantes):
            interes = round(saldo_real * (tasa_mensual / 100), 2)
            
            # Amortización del mes
            if i == cuota_inicio + cuotas_restantes - 1:
                amort = saldo_repartir # Última cuota liquida lo que quede
            else:
                amort = amort_base
            
            cuota_total = round(amort + interes, 2)
            
            plan.append({
                "cuota": i,
                "saldo_inicial": round(saldo_real, 2),
                "interes": interes,
                "amortizacion_programada": amort,
                "abono_extra": 0.0,
                "total_pagado": 0.0,
                "interes_pagado_real": 0.0,
                "capital_pagado_real": 0.0,
                "cuota_total": cuota_total,
                "saldo_final": max(0.0, round(saldo_real - amort, 2)),
                "estado": "PENDIENTE",
                "fecha_pago": None
            })
            
            saldo_repartir = round(saldo_repartir - amort, 2)
            saldo_real = round(saldo_real - amort, 2)
            
        return plan

    @staticmethod
    async def crear_prestamo(socio_id: str, unica_id: str, capital_original: float, meses_originales: int, bypasar_liquidez: bool = False):
        from repositories.base_repo import caja_repo, accion_repo, prestamo_repo
        
        # 1. Validaciones de Configuración
        config = await config_repo.get_one({"unica_id": unica_id})
        if not config: raise BusinessError("Configuración no encontrada para la UNICA")
        tasa_mensual = config.get("porcentaje_interes_prestamo", 3.0)
        
        socio = await socio_repo.get_by_id(socio_id)
        if not socio: raise BusinessError("Socio no encontrado")

        # 2. El socio puede tener múltiples préstamos activos (habilitado por requerimiento)

        # 3. Calcular Saldo Real en Caja (Bóveda) para verificar liquidez
        # Flujos de entrada/salida manuales
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        ingresos_caja = sum(f["monto"] for f in flujos if f["tipo"] == "INGRESO")
        egresos_caja = sum(f["monto"] for f in flujos if f["tipo"] == "EGRESO")

        # Movimientos de acciones (Compra = Ingreso a caja, Venta = Egreso)
        acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        ingresos_acciones = sum(a["cantidad"] * a.get("valor_unitario", 20) for a in acciones if a["tipo"] == "COMPRA")
        egresos_acciones = sum(abs(a["cantidad"]) * a.get("valor_unitario", 20) for a in acciones if a["tipo"] == "VENTA")

        # Préstamos (Desembolsos = Egreso, Pagos = Ingreso)
        todos_prestamos = await prestamo_repo.get_all({"unica_id": unica_id})
        desembolsos = 0
        pagos_recibidos = 0
        for p in todos_prestamos:
            if p.get("estado") != "ANULADO":
                desembolsos += p.get("capital_original", 0)
                for pago in p.get("historial_pagos", []):
                    pagos_recibidos += pago.get("monto_total", 0)

        saldo_real_caja = (ingresos_caja + ingresos_acciones + pagos_recibidos) - (egresos_caja + egresos_acciones + desembolsos)
        if not bypasar_liquidez and capital_original > saldo_real_caja:
            raise BusinessError(f"Fondos insuficientes. Saldo en bóveda: S/ {round(saldo_real_caja, 2)}. El capital solicitado es S/ {capital_original}")

        # 4. Generar Préstamo
        cronograma = PrestamoService._calcular_plan_decreciente(capital_original, tasa_mensual, meses_originales, 1)

        prestamo_data = {
            "unica_id": unica_id,
            "socio_id": socio_id,
            "capital_original": round(capital_original, 2),
            "meses_originales": meses_originales,
            "tasa_mensual": round(tasa_mensual, 2),
            "tipo_calculo": "saldo_decreciente",
            "saldo_actual": round(capital_original, 2),
            "monto_pagado_capital": 0.0,
            "total_interes_pagado": 0.0,
            "estado": "ACTIVO",
            "cronograma": cronograma,
            "historial_pagos": [],
            "fecha_creacion": datetime.now()
        }
        
        return await prestamo_repo.create(prestamo_data)
        
    @staticmethod
    async def listar_vigentes(unica_id: str):
        # Mantenemos el filtro de estado ACTIVO
        prestamos = await prestamo_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        for p in prestamos:
            socio = await socio_repo.get_by_id(p["socio_id"])
            p["socio_nombre"] = f"{socio['nombres']} {socio['apellidos']}" if socio else "Socio Desconocido"
            # Alias para retrocompatibilidad básica si el front busca campos antiguos
            p["monto_principal"] = p["capital_original"]
            p["saldo_pendiente"] = p["saldo_actual"]
            p["cuotas_totales"] = p["meses_originales"]
            p["interes_porcentaje_mensual"] = p["tasa_mensual"]
            p["plan_pagos"] = p["cronograma"]
        return prestamos

    @staticmethod
    async def registrar_pago(prestamo_id: str, numero_cuota: int, monto_pagado_total: float):
        """
        Lógica financiera flexible con PRIORIDAD DE INTERÉS:
        1. Cubrir interés del período primero.
        2. El excedente cubre la amortización programada.
        3. Si sobra más, es Abono Extra (deduce capital futuro).
        4. No es obligatorio pagar la cuota completa.
        """
        prestamo = await prestamo_repo.get_by_id(prestamo_id)
        if not prestamo: raise BusinessError("Préstamo no encontrado")
        if prestamo["estado"] in ["CANCELADO", "ANULADO"]: 
            raise BusinessError(f"El préstamo está {prestamo['estado']}")
        
        cronograma = prestamo.get("cronograma", [])
        idx = -1
        for i, c in enumerate(cronograma):
            if c["cuota"] == numero_cuota:
                idx = i
                break
        
        if idx == -1: raise BusinessError("Cuota no encontrada en el cronograma")
        if cronograma[idx]["estado"] == "PAGADO": raise BusinessError("Esta cuota ya fue pagada")

        if monto_pagado_total <= 0: raise BusinessError("El monto a pagar debe ser mayor a cero")
        
        monto_pagado_total = round(monto_pagado_total, 2)
        cuota_prog = cronograma[idx]
        
        # --- VALIDACIÓN DE ÚLTIMA CUOTA ---
        # Si es la última cuota del cronograma, debe pagar el total para cerrar el préstamo
        es_ultima_cuota = (idx == len(cronograma) - 1)
        
        # 1. ¿Cuánto se debe de interés en esta cuota?
        interes_total_cuota = cuota_prog["interes"]
        interes_ya_pagado = cuota_prog.get("interes_pagado_real", 0.0)
        interes_pendiente = round(interes_total_cuota - interes_ya_pagado, 2)

        # 2. ¿Cuánto se debe de capital programado?
        capital_total_cuota = cuota_prog["amortizacion_programada"]
        capital_ya_pagado = cuota_prog.get("capital_pagado_real", 0.0)
        capital_pendiente = round(capital_total_cuota - capital_ya_pagado, 2)

        if es_ultima_cuota:
            total_deuda_final = round(interes_pendiente + capital_pendiente, 2)
            if monto_pagado_total < total_deuda_final:
                raise BusinessError(f"Es la última cuota. Debe liquidar el saldo total de S/ {total_deuda_final}")

        pago_a_interes = min(monto_pagado_total, interes_pendiente)
        sobrante = round(monto_pagado_total - pago_a_interes, 2)

        pago_a_capital_prog = min(sobrante, capital_pendiente)
        sobrante = round(sobrante - pago_a_capital_prog, 2)

        # 3. Abono Extra (Excedente absoluto)
        abono_extra = 0.0
        if sobrante > 0:
            abono_extra = min(sobrante, round(prestamo["saldo_actual"] - (capital_pendiente if capital_pendiente > 0 else 0), 2))
            sobrante = round(sobrante - abono_extra, 2)

        # Actualizar acumuladores de la cuota
        cronograma[idx]["interes_pagado_real"] = round(interes_ya_pagado + pago_a_interes, 2)
        cronograma[idx]["capital_pagado_real"] = round(capital_ya_pagado + pago_a_capital_prog, 2)
        cronograma[idx]["total_pagado"] = round(cronograma[idx].get("total_pagado", 0) + monto_pagado_total - sobrante, 2)
        
        # Siempre cerramos la cuota según solicitud del usuario para no dejar parciales.
        # Esto significa que el slot de este mes se considera atendido y el capital no pagado 
        # se redistribuirá en el recalculo automático del paso 4.
        cronograma[idx]["estado"] = "PAGADO"
        cronograma[idx]["fecha_pago"] = datetime.now().isoformat()

        # Actualizar saldos globales del préstamo
        capital_amortizado_en_este_pago = round(pago_a_capital_prog + abono_extra, 2)
        nuevo_saldo = round(prestamo["saldo_actual"] - capital_amortizado_en_este_pago, 2)

        pago_log = {
            "fecha": datetime.now(),
            "monto_total": round(monto_pagado_total - sobrante, 2),
            "monto_interes": pago_a_interes,
            "monto_capital": round(pago_a_capital_prog + abono_extra, 2),
            "interes": pago_a_interes,
            "amort_prog": pago_a_capital_prog,
            "abono_extra": abono_extra,
            "saldo_despues": max(0.0, nuevo_saldo)
        }

        # 4. Recalcular plan futuro para asegurar Saldo Decreciente Real
        cuotas_restantes = len(cronograma) - (idx + 1)
        if nuevo_saldo > 0 and cuotas_restantes > 0:
            # Dado que cerramos la cuota actual (idx) como PAGADO,
            # todo el saldo que queda pendiente (nuevo_saldo) debe ser 
            # redistribuido equitativamente entre las cuotas que faltan.
            plan_futuro = PrestamoService._calcular_plan_decreciente(
                round(nuevo_saldo, 2),
                prestamo["tasa_mensual"],
                cuotas_restantes,
                numero_cuota + 1,
                saldo_interes=nuevo_saldo # El interés se calcula sobre la deuda real total
            )
            cronograma = cronograma[:idx+1] + plan_futuro
        elif nuevo_saldo <= 0:
            cronograma = cronograma[:idx+1]
            prestamo["estado"] = "CANCELADO"

        update_data = {
            "cronograma": cronograma,
            "saldo_actual": max(0.0, nuevo_saldo),
            "monto_pagado_capital": round(prestamo.get("monto_pagado_capital", 0) + capital_amortizado_en_este_pago, 2),
            "total_interes_pagado": round(prestamo.get("total_interes_pagado", 0) + pago_a_interes, 2),
            "estado": "CANCELADO" if nuevo_saldo <= 0 else "ACTIVO",
            "historial_pagos": prestamo.get("historial_pagos", []) + [pago_log]
        }
        
        return await prestamo_repo.update({"_id": ObjectId(prestamo_id)}, update_data)

    @staticmethod
    async def anular_prestamo(prestamo_id: str, motivo: str = "Anulado por el administrador"):
        prestamo = await prestamo_repo.get_by_id(prestamo_id)
        if not prestamo: raise BusinessError("Préstamo no encontrado")
        
        if prestamo.get("monto_pagado_capital", 0) > 0 or prestamo.get("total_interes_pagado", 0) > 0:
            raise BusinessError("No se puede anular un préstamo que ya tiene pagos. Considere cancelarlo anticipadamente.")

        if prestamo["estado"] == "ANULADO":
            raise BusinessError("Este préstamo ya está anulado")

        update_data = {
            "estado": "ANULADO",
            "motivo_anulacion": motivo,
            "fecha_anulacion": datetime.now()
        }
        return await prestamo_repo.update({"_id": ObjectId(prestamo_id)}, update_data)

    @staticmethod
    async def actualizar_prestamo(prestamo_id: str, data: dict):
        prestamo = await prestamo_repo.get_by_id(prestamo_id)
        if not prestamo: raise BusinessError("Préstamo no encontrado")

        # Permitir editar solo si no tiene pagos? 
        # El usuario pidió poder editarlo libremente si hay errores.
        
        capital = data.get("capital_original", prestamo["capital_original"])
        meses = data.get("meses_originales", prestamo["meses_originales"])
        tasa = data.get("tasa_mensual", prestamo["tasa_mensual"])
        estado = data.get("estado", prestamo["estado"])

        # Si cambió algo clave, regenerar cronograma (si no hay pagos)
        cronograma = prestamo["cronograma"]
        if (capital != prestamo["capital_original"] or meses != prestamo["meses_originales"] or tasa != prestamo["tasa_mensual"]):
            if prestamo.get("monto_pagado_capital", 0) > 0:
                # Si ya hay pagos, solo permitimos edición manual de saldos/metadatos o avisamos
                pass 
            else:
                cronograma = PrestamoService._calcular_plan_decreciente(capital, tasa, meses, 1)

        update_data = {
            "capital_original": round(capital, 2),
            "meses_originales": meses,
            "tasa_mensual": round(tasa, 2),
            "estado": estado,
            "cronograma": cronograma,
            "saldo_actual": round(capital - prestamo.get("monto_pagado_capital", 0), 2)
        }

        # Permitir sobreescribir campos específicos del cronograma si se envían
        if "cronograma" in data:
            update_data["cronograma"] = data["cronograma"]

        return await prestamo_repo.update({"_id": ObjectId(prestamo_id)}, update_data)

    @staticmethod
    async def obtener_reporte_completo(unica_id: str):
        # Obtener todos los préstamos sin filtrar por estado
        prestamos = await prestamo_repo.get_all({"unica_id": unica_id})
        for p in prestamos:
            socio = await socio_repo.get_by_id(p["socio_id"])
            p["socio_nombre"] = f"{socio['nombres']} {socio['apellidos']}" if socio else "Socio Desconocido"
        
        # Ordenar por fecha de creación descendente
        prestamos.sort(key=lambda x: x.get("fecha_creacion", datetime.min), reverse=True)
        return prestamos
