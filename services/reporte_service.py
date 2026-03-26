import datetime
from repositories.base_repo import caja_repo, transaccion_repo, socio_repo, prestamo_repo, accion_repo

class ReporteService:

    @staticmethod
    async def obtener_metricas_dashboard(unica_id: str):
        now = datetime.datetime.now()
        anio_actual = now.year
        
        def get_dt(val):
            if isinstance(val, datetime.datetime): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        # 1. Capital Social (Dinero de acciones)
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        total_acciones = 0
        capital_social = 0
        for m in mov_acciones:
            total_acciones += m.get("cantidad", 0)
            if m.get("tipo") == "COMPRA":
                capital_social += m.get("cantidad", 0) * m.get("valor_unitario", 20)
            elif m.get("tipo") == "VENTA":
                capital_social -= abs(m.get("cantidad", 0)) * m.get("valor_unitario", 20)

        # 2. Caja de Utilidades (Intereses + Otros Ingresos - Otros Gastos)
        # Intereses Recaudados
        prestamos_all = await prestamo_repo.get_all({"unica_id": unica_id})
        total_intereses_recaudados = 0
        for p in prestamos_all:
            if p.get("estado") != "ANULADO":
                total_intereses_recaudados += p.get("total_interes_pagado", 0)

        # Otros flujos (Multas, Gastos Admin, etc)
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        otros_ingresos = sum(f["monto"] for f in flujos if f["tipo"] == "INGRESO")
        otros_gastos = sum(f["monto"] for f in flujos if f["tipo"] == "EGRESO")
        
        caja_utilidades = total_intereses_recaudados + otros_ingresos - otros_gastos

        # 3. Liquidez Total (Bóveda)
        # Es el capital social + utilidades - lo que está prestado actualmente
        # Pero ojo, los pagos de capital de préstamos regresan a la boveda.
        # Una forma más directa de calcular la liquidez real es:
        # (Capital Social + Intereses Recibidos + Capital Recuperado + Otros Ingresos) - (Desembolsos + Retiros Acciones + Otros Gastos)
        
        capital_recuperado_total = 0
        total_desembolsado = 0
        for p in prestamos_all:
            if p.get("estado") != "ANULADO":
                total_desembolsado += p.get("capital_original", 0)
                capital_recuperado_total += p.get("monto_pagado_capital", 0)

        total_boveda = (capital_social + total_intereses_recaudados + capital_recuperado_total + otros_ingresos) - (total_desembolsado + otros_gastos)

        # 4. Datos del Gráfico (Año Actual)
        chart_data = []
        meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
        for i in range(1, 13):
            # Ingresos combinados
            ing_acciones = sum(m.get("cantidad", 0) * m.get("valor_unitario", 20) for m in mov_acciones if get_dt(m.get("fecha")) and get_dt(m["fecha"]).month == i and get_dt(m["fecha"]).year == anio_actual and m["tipo"] == "COMPRA")
            ing_f = sum(f["monto"] for f in flujos if get_dt(f.get("fecha")) and get_dt(f["fecha"]).month == i and get_dt(f["fecha"]).year == anio_actual and f["tipo"] == "INGRESO")
            ing_p = 0
            for p in prestamos_all:
                for h in p.get("historial_pagos", []):
                    dt_h = get_dt(h.get("fecha"))
                    if dt_h and dt_h.month == i and dt_h.year == anio_actual:
                        ing_p += h.get("monto_total", 0)
            
            # Egresos combinados
            egr_f = sum(f["monto"] for f in flujos if get_dt(f.get("fecha")) and get_dt(f["fecha"]).month == i and get_dt(f["fecha"]).year == anio_actual and f["tipo"] == "EGRESO")
            egr_p = sum(p.get("capital_original", 0) for p in prestamos_all if get_dt(p.get("fecha_creacion")) and get_dt(p["fecha_creacion"]).month == i and get_dt(p["fecha_creacion"]).year == anio_actual)
            egr_acciones = sum(abs(m.get("cantidad", 0)) * m.get("valor_unitario", 20) for m in mov_acciones if get_dt(m.get("fecha")) and get_dt(m["fecha"]).month == i and get_dt(m["fecha"]).year == anio_actual and m["tipo"] == "VENTA")

            chart_data.append({
                "name": meses_nombres[i-1],
                "ingresos": round(ing_acciones + ing_f + ing_p, 2),
                "egresos": round(egr_f + egr_p + egr_acciones, 2)
            })

        # 4. Total Socios
        socios_all = await socio_repo.get_all({"unica_id": unica_id, "estado": "Activo"})
        total_socios = len(socios_all)

        return {
            "total_socios": total_socios,
            "total_capital_social": round(capital_social, 2),
            "total_caja_utilidades": round(caja_utilidades, 2),
            "total_boveda": round(total_boveda, 2),
            "total_acciones": total_acciones,
            "monto_prestado_activo": round(sum(p.get("saldo_actual", 0) for p in prestamos_all if p.get("estado") == "ACTIVO"), 2),
            "recuento_prestamos": len([p for p in prestamos_all if p.get("estado") == "ACTIVO"]),
            "chart_data": chart_data
        }

    @staticmethod
    async def obtener_balance_mensual(unica_id: str, mes: int, anio: int):
        import datetime
        def get_dt(val):
            if isinstance(val, (datetime.datetime, datetime.date)): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        # 1. Ingresos por Acciones (Ventas reales)
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        ingreso_acciones = 0
        retiro_acciones = 0
        for m in mov_acciones:
            dt_m = get_dt(m.get("fecha"))
            if dt_m and dt_m.month == mes and dt_m.year == anio:
                if m["tipo"] == "COMPRA":
                    ingreso_acciones += m["cantidad"] * m.get("valor_unitario", 20)
                elif m["tipo"] == "VENTA":
                    retiro_acciones += abs(m["cantidad"]) * m.get("valor_unitario", 20)
        
        # 2. Flujos directos ACTIVOS
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"}) 
        mes_flujos = []
        for f in flujos:
            dt_f = get_dt(f.get("fecha"))
            if dt_f and dt_f.month == mes and dt_f.year == anio:
                mes_flujos.append(f)
        ingresos_extra = sum(f["monto"] for f in mes_flujos if f["tipo"] == "INGRESO")
        egresos_extra = sum(f["monto"] for f in mes_flujos if f["tipo"] == "EGRESO")

        # 3. Datos Reales de Préstamos
        prestamos = await prestamo_repo.get_all({"unica_id": unica_id})
        interes_prestamos = 0
        capital_recuperado = 0
        prestamos_otorgados = 0

        for p in prestamos:
            # Pagos recibidos en el mes
            for h in p.get("historial_pagos", []):
                dt_h = get_dt(h.get("fecha"))
                if dt_h and dt_h.month == mes and dt_h.year == anio:
                    interes_prestamos += h.get("monto_interes") or h.get("interes", 0)
                    capital_recuperado += h.get("monto_capital") or (h.get("amort_prog", 0) + h.get("abono_extra", 0))
            
            # Desembolsos realizados en el mes
            dt_p = get_dt(p.get("fecha_creacion"))
            if dt_p and dt_p.month == mes and dt_p.year == anio:
                prestamos_otorgados += p.get("capital_original", 0)

        total_ingresos = ingreso_acciones + interes_prestamos + capital_recuperado + ingresos_extra
        total_egresos = retiro_acciones + prestamos_otorgados + egresos_extra
        balance_final = total_ingresos - total_egresos

        return {
            "periodo": f"{mes}/{anio}",
            "ahorros_capital": round(ingreso_acciones, 2),
            "intereses_totales": round(interes_prestamos, 2),
            "capital_recuperado": round(capital_recuperado, 2),
            "retiros_socios": round(retiro_acciones, 2),
            "prestamos_nuevos": round(prestamos_otorgados, 2),
            "otros_ingresos": round(ingresos_extra, 2),
            "otros_egresos": round(egresos_extra, 2),
            "total_ingresos": round(total_ingresos, 2),
            "total_egresos": round(total_egresos, 2),
            "balance_utilidad": round(balance_final, 2)
        }

    @staticmethod
    async def obtener_reparticion_utilidades(unica_id: str, anio: int):
        from repositories.base_repo import config_repo
        import datetime
        from dateutil.relativedelta import relativedelta
        import math
        
        def get_dt(val):
            if isinstance(val, (datetime.datetime, datetime.date)): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        # 0. Determinar el Rango del Ciclo Contable
        config = await config_repo.get_one({"unica_id": unica_id})
        mes_inicio_ciclo = config.get("mes_inicio_ciclo", 1) if config else 1
        
        fecha_inicio_ciclo = datetime.datetime(anio, mes_inicio_ciclo, 1)
        fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(years=1) - relativedelta(seconds=1)

        # 1. Utilidad por Intereses (Solo los pagados dentro del ciclo contable)
        prestamos = await prestamo_repo.get_all({"unica_id": unica_id})
        total_interes = 0
        for p in prestamos:
            if p.get("estado") == "ANULADO": continue
            for h in p.get("historial_pagos", []):
                dt_h = get_dt(h.get("fecha"))
                if dt_h and fecha_inicio_ciclo <= dt_h <= fecha_fin_ciclo:
                    total_interes += h.get("monto_interes") or h.get("interes", 0)

        # 2. Utilidad por Otros Conceptos (Solo del ciclo)
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        ingresos_extra = 0
        egresos_extra = 0
        for f in flujos:
            dt_f = get_dt(f.get("fecha"))
            if dt_f and fecha_inicio_ciclo <= dt_f <= fecha_fin_ciclo:
                if f["tipo"] == "INGRESO": ingresos_extra += f["monto"]
                else: egresos_extra += f["monto"]

        utilidad_bruta = total_interes + ingresos_extra
        gastos_acumulados = egresos_extra
        utilidad_neta = utilidad_bruta - gastos_acumulados
        reserva_legal = utilidad_neta * 0.10 if utilidad_neta > 0 else 0
        utilidad_distribuible = utilidad_neta - reserva_legal

        # 3. Acciones por Socio usando el Método "Acciones-Mes"
        socios = await socio_repo.get_all({"unica_id": unica_id, "estado": "Activo"})
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        
        total_acciones_mes_sistema = 0.0
        total_acciones_sistema_al_cierre = 0

        # Función auxiliar para calcular meses trabajados
        def meses_trabajados_en_ciclo(fecha_dt):
            # Según el Excel de UNICA:
            # - Las acciones del "Mes 0" (antes del ciclo) o saldo anterior trabajan 12 meses.
            # - Las acciones compradas en el "Mes 1" del ciclo (ej. Junio 2025) trabajan 11 meses.
            # - Las compradas en el "Mes 2" trabajan 10 meses, y así sucesivamente...
            # - Las compradas en el "Mes 12" trabajan 0 meses en la repartición actual (o 1, revisar).
            # Revisando el Excel: "2025-06-07" tiene multiplier = 11. "2026-05-07" tiene multiplier = 0.
            
            if fecha_dt < fecha_inicio_ciclo:
                return 12  # Cómputo total para el capital arrastrado
            if fecha_dt > fecha_fin_ciclo:
                return 0
            
            mes_diferencia = (fecha_dt.year - fecha_inicio_ciclo.year) * 12 + (fecha_dt.month - fecha_inicio_ciclo.month)
            # La diferencia es 0 para el primer mes del ciclo.
            # Según Excel, si compras en el Mes 1 (diferencia 0), te multiplican por 11.
            return max(0, 11 - mes_diferencia)

        # Calcular totales globales
        for m in mov_acciones:
            dt_m = get_dt(m.get("fecha"))
            if dt_m and dt_m <= fecha_fin_ciclo:
                cant = m.get("cantidad", 0)
                meses_t = meses_trabajados_en_ciclo(dt_m)
                
                total_acciones_sistema_al_cierre += cant
                if cant > 0:
                    total_acciones_mes_sistema += (cant * meses_t)
                else:
                    total_acciones_mes_sistema += (cant * meses_t) # cant es negativo en VENTAS
        
        valor_por_accion_mes = utilidad_distribuible / total_acciones_mes_sistema if total_acciones_mes_sistema > 0 else 0
        valor_por_accion_plana = utilidad_distribuible / total_acciones_sistema_al_cierre if total_acciones_sistema_al_cierre > 0 else 0

        reparticion_detallada = []
        for s in socios:
            acciones_socio_cierre = 0
            acciones_mes_socio = 0.0
            
            s_id_str = str(s["_id"])
            for m in mov_acciones:
                if str(m.get("socio_id")) == s_id_str:
                    dt_m = get_dt(m.get("fecha"))
                    if dt_m and dt_m <= fecha_fin_ciclo:
                        cant = m.get("cantidad", 0)
                        meses_t = meses_trabajados_en_ciclo(dt_m)
                        
                        acciones_socio_cierre += cant
                        acciones_mes_socio += (cant * meses_t)
            
            if acciones_socio_cierre > 0 or acciones_mes_socio > 0:
                ganancia = acciones_mes_socio * valor_por_accion_mes
                
                # Verificar si tiene deuda activa
                p_activo = await prestamo_repo.get_one({
                    "socio_id": s_id_str,
                    "estado": "ACTIVO"
                })

                reparticion_detallada.append({
                    "socio_id": s_id_str,
                    "nombres": f"{s['nombres']} {s['apellidos']}",
                    "dni": s["dni"],
                    "acciones_al_cierre": acciones_socio_cierre,
                    "acciones_mes_acumuladas": round(acciones_mes_socio, 2),
                    # El porcentaje visual es sobre la utilidad/las acciones-mes en este algoritmo
                    "porcentaje_participacion": round((acciones_mes_socio / total_acciones_mes_sistema * 100) if total_acciones_mes_sistema > 0 else 0, 2),
                    "monto_utilidad": round(ganancia, 2),
                    "tiene_deuda": p_activo is not None
                })

        from repositories.base_repo import reparticion_repo
        existente = await reparticion_repo.get_one({"unica_id": unica_id, "anio": anio})

        return {
            "resumen": {
                "anio": anio,
                "total_interes_prestamos": round(total_interes, 2),
                "otros_ingresos": round(ingresos_extra, 2),
                "utilidad_bruta": round(utilidad_bruta, 2),
                "gastos_acumulados": round(gastos_acumulados, 2),
                "utilidad_neta": round(utilidad_neta, 2),
                "reserva_legal_10": round(reserva_legal, 2),
                "utilidad_distribuible": round(utilidad_distribuible, 2),
                "total_acciones_sistema": total_acciones_sistema_al_cierre,
                "total_acciones_mes_sistema": round(total_acciones_mes_sistema, 2),
                "valor_por_accion": round(valor_por_accion_plana, 4), # Dejamos el plano original por si el front lo espera
                "valor_por_accion_mes": round(valor_por_accion_mes, 6),
                "esta_cerrado": existente is not None,
                "fecha_cierre": existente.get("fecha_registro") if existente else None
            },
            "detalle_socios": sorted(reparticion_detallada, key=lambda x: x["monto_utilidad"], reverse=True)
        }

    @staticmethod
    async def registrar_reparticion(data: dict):
        # Evitar duplicados por año
        existente = await reparticion_repo.get_one({"unica_id": data["unica_id"], "anio": data["anio"]})
        if existente:
            raise Exception(f"El cierre del año {data['anio']} ya ha sido registrado.")
        
        # Guardar el registro de reparticion
        res = await reparticion_repo.create(data)

        # Lógica de CIERRE CONTABLE: 
        # Para que la "Caja de Utilidades" quede en cero para el nuevo año,
        # registramos un EGRESO por el total de la utilidad bruta repartida.
        flujo_cierre = {
            "unica_id": data["unica_id"],
            "tipo": "EGRESO",
            "categoria": "Reparto de Utilidades",
            "monto": data["utilidad_bruta"],
            "descripcion": f"Cierre contable y reparto de utilidades del año {data['anio']}",
            "fecha": datetime.datetime.now(),
            "estado": "ACTIVO"
        }
        await caja_repo.create(flujo_cierre)
        
        return res

    @staticmethod
    async def capitalizar_utilidad(unica_id: str, socio_id: str, monto: float, anio: int):
        from services.accion_service import AccionService
        from repositories.base_repo import config_repo
        
        config = await config_repo.get_one({"unica_id": unica_id})
        valor_accion = config.get("valor_accion", 20.0) if config else 20.0
        
        # Calcular acciones (pueden ser decimales si el sistema lo permite, pero usualmente son enteros)
        cantidad_acciones = int(monto / valor_accion)
        sobrante = monto % valor_accion
        
        motivo = f"Capitalización de utilidades {anio}"
        if sobrante > 0:
            motivo += f" (Sobrante S/ {round(sobrante, 2)} no capitalizado)"

        if cantidad_acciones <= 0:
            raise Exception(f"El monto S/ {monto} es insuficiente para capitalizar al menos 1 acción (S/ {valor_accion})")

        return await AccionService.registrar_movimiento(
            unica_id=unica_id,
            socio_id=socio_id,
            cantidad=cantidad_acciones,
            tipo="COMPRA",
            motivo=motivo
        )

    @staticmethod
    async def cobrar_deuda_con_utilidad(unica_id: str, socio_id: str, monto_utilidad: float, anio: int):
        from services.prestamo_service import PrestamoService
        from repositories.base_repo import prestamo_repo
        
        # Buscar préstamos activos del socio
        prestamos_activos = await prestamo_repo.get_all({
            "unica_id": unica_id,
            "socio_id": socio_id,
            "estado": "ACTIVO"
        })
        
        if not prestamos_activos:
            raise Exception("El socio no tiene préstamos activos para cobrar.")

        monto_restante = monto_utilidad
        pagos_realizados = []

        for p in prestamos_activos:
            if monto_restante <= 0: break
            
            # Ordenar cuotas pendientes por número
            cronograma = p.get("cronograma", [])
            cuotas_pendientes = [c for c in cronograma if c["estado"] == "PENDIENTE"]
            cuotas_pendientes.sort(key=lambda x: x["cuota"])
            
            for cuota in cuotas_pendientes:
                if monto_restante <= 0: break
                
                # Cuánto se debe en esta cuota?
                int_pend = round(cuota["interes"] - cuota.get("interes_pagado_real", 0.0), 2)
                cap_pend = round(cuota["amortizacion_programada"] - cuota.get("capital_pagado_real", 0.0), 2)
                total_cuota = round(int_pend + cap_pend, 2)
                
                if total_cuota <= 0: continue

                pago_a_realizar = min(monto_restante, total_cuota)
                
                # Registrar el pago
                await PrestamoService.registrar_pago(
                    prestamo_id=str(p["_id"]),
                    numero_cuota=cuota["cuota"],
                    monto_pagado_total=pago_a_realizar
                )
                
                monto_restante = round(monto_restante - pago_a_realizar, 2)
                pagos_realizados.append({
                    "prestamo_id": str(p["_id"]),
                    "cuota": cuota["cuota"],
                    "monto": pago_a_realizar
                })

        return {
            "status": "success",
            "monto_original": monto_utilidad,
            "monto_aplicado": round(monto_utilidad - monto_restante, 2),
            "monto_sobrante": monto_restante,
            "pagos": pagos_realizados
        }

    @staticmethod
    async def listar_reparticiones_historicas(unica_id: str):
        from repositories.base_repo import reparticion_repo
        items = await reparticion_repo.get_all({"unica_id": unica_id})
        items.sort(key=lambda x: x.get("anio", 0), reverse=True)
        return items

    @staticmethod
    async def obtener_indicadores_salud(unica_id: str):
        import datetime
        now = datetime.datetime.now()
        
        def get_dt(val):
            if isinstance(val, (datetime.datetime, datetime.date)): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        # 1. Obtener toda la data necesaria
        prestamos_all = await prestamo_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        
        # 2. Cartera Total y Mora (PAR)
        cartera_total = sum(p.get("saldo_actual", 0) for p in prestamos_all)
        cartera_en_mora = 0
        
        for p in prestamos_all:
            fecha_inicio = get_dt(p.get("fecha_creacion"))
            if not fecha_inicio: continue
            
            es_mora = False
            cronograma = p.get("cronograma", [])
            for cuota in cronograma:
                if cuota.get("estado") == "PENDIENTE":
                    # Estimar vencimiento: fecha_inicio + N meses
                    n_mes = cuota.get("cuota", 1)
                    # Simple addition of months
                    y = fecha_inicio.year + (fecha_inicio.month + n_mes - 1) // 12
                    m = (fecha_inicio.month + n_mes - 1) % 12 + 1
                    vencimiento = datetime.datetime(y, m, min(fecha_inicio.day, 28)) # Safe day
                    
                    if vencimiento < now:
                        es_mora = True
                        break
            
            if es_mora:
                cartera_en_mora += p.get("saldo_actual", 0)
        
        indice_mora = (cartera_en_mora / cartera_total * 100) if cartera_total > 0 else 0
        
        # 3. Liquidez y Bóveda
        # (Reutilizamos lógica del dashboard para consistencia)
        capital_social = 0
        for m in mov_acciones:
            if m.get("tipo") == "COMPRA":
                capital_social += m.get("cantidad", 0) * m.get("valor_unitario", 20)
            elif m.get("tipo") == "VENTA":
                capital_social -= abs(m.get("cantidad", 0)) * m.get("valor_unitario", 20)

        total_intereses = sum(p.get("total_interes_pagado", 0) for p in (await prestamo_repo.get_all({"unica_id": unica_id})) if p.get("estado") != "ANULADO")
        ingresos_f = sum(f["monto"] for f in flujos if f["tipo"] == "INGRESO")
        egresos_f = sum(f["monto"] for f in flujos if f["tipo"] == "EGRESO")
        utilidades = total_intereses + ingresos_f - egresos_f
        
        # Liquidez real (Bóveda)
        cap_recuperado = sum(p.get("monto_pagado_capital", 0) for p in (await prestamo_repo.get_all({"unica_id": unica_id})) if p.get("estado") != "ANULADO")
        total_desembolsado = sum(p.get("capital_original", 0) for p in (await prestamo_repo.get_all({"unica_id": unica_id})) if p.get("estado") != "ANULADO")
        boveda = (capital_social + total_intereses + cap_recuperado + ingresos_f) - (total_desembolsado + egresos_f)
        
        liquidez_ratio = (boveda / (capital_social + utilidades) * 100) if (capital_social + utilidades) > 0 else 0
        
        # 4. Productividad del Capital
        productividad = (cartera_total / capital_social * 100) if capital_social > 0 else 0
        
        return {
            "indice_mora": round(indice_mora, 2),
            "cartera_total": round(cartera_total, 2),
            "cartera_en_mora": round(cartera_en_mora, 2),
            "liquidez_ratio": round(liquidez_ratio, 2),
            "capital_social": round(capital_social, 2),
            "utilidades_acumuladas": round(utilidades, 2),
            "boveda_actual": round(boveda, 2),
            "productividad_capital": round(productividad, 2),
            "status_mora": "PELIGRO" if indice_mora > 10 else "ALERTA" if indice_mora > 5 else "SALUDABLE",
            "status_liquidez": "CRÍTICA" if liquidez_ratio < 10 else "BAJA" if liquidez_ratio < 20 else "SALUDABLE"
        }

    @staticmethod
    async def obtener_analitica_avanzada(unica_id: str):
        import datetime
        now = datetime.datetime.now()
        meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
        
        def get_dt(val):
            if isinstance(val, (datetime.datetime, datetime.date)): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        # Cargar todo de una vez para filtrar en memoria
        socio_all = await socio_repo.get_all({"unica_id": unica_id})
        prestamos_all = await prestamo_repo.get_all({"unica_id": unica_id})
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        flujos = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})

        # --- 1. EVOLUCIÓN DEL PATRIMONIO (Últimos 12 meses) ---
        # --- 3. MIX DE INGRESOS (Mensual) ---
        # --- 5. TENDENCIA MORA (Últimos 6 meses) ---
        
        datos_mensuales = []
        acum_capital = 0
        acum_utilidad = 0
        
        # Calcular capital inicial antes del año actual para el acumulado
        for m in mov_acciones:
            dt_m = get_dt(m.get("fecha"))
            if dt_m and dt_m.year < now.year:
                monto = m.get("cantidad", 0) * m.get("valor_unitario", 20)
                if m["tipo"] == "COMPRA": acum_capital += monto
                else: acum_capital -= abs(monto)

        for i in range(1, now.month + 1):
            # Capital del mes
            mes_cap = sum((m.get("cantidad", 0) * m.get("valor_unitario", 20)) if m["tipo"] == "COMPRA" else -(abs(m.get("cantidad", 0)) * m.get("valor_unitario", 20)) 
                          for m in mov_acciones if get_dt(m.get("fecha")) and get_dt(m["fecha"]).month == i and get_dt(m["fecha"]).year == now.year)
            
            # Ingresos del mes (Mix)
            mes_interes = 0
            for p in prestamos_all:
                if p.get("estado") == "ANULADO": continue
                for h in p.get("historial_pagos", []):
                    dt_h = get_dt(h.get("fecha"))
                    if dt_h and dt_h.month == i and dt_h.year == now.year:
                        mes_interes += h.get("monto_interes") or h.get("interes", 0)
            
            mes_otros_ing = sum(f["monto"] for f in flujos if get_dt(f.get("fecha")) and get_dt(f["fecha"]).month == i and get_dt(f["fecha"]).year == now.year and f["tipo"] == "INGRESO")
            mes_gastos = sum(f["monto"] for f in flujos if get_dt(f.get("fecha")) and get_dt(f["fecha"]).month == i and get_dt(f["fecha"]).year == now.year and f["tipo"] == "EGRESO")
            
            mes_utilidad = mes_interes + mes_otros_ing - mes_gastos
            
            acum_capital += mes_cap
            acum_utilidad += mes_utilidad
            
            # Cálculo de Mora Mensual (Retroactivo simple: préstamos creados hasta ese mes que no terminaron)
            cartera_mes = 0
            mora_mes = 0
            for p in prestamos_all:
                dt_creacion = get_dt(p.get("fecha_creacion"))
                if not dt_creacion or dt_creacion.year > now.year or (dt_creacion.year == now.year and dt_creacion.month > i): continue
                if p.get("estado") == "ANULADO": continue
                
                # Saldo estimado al final de ese mes (muy simplificado)
                saldo_p_mes = p.get("capital_original", 0)
                pagado_hasta_mes = sum((h.get("monto_capital") or (h.get("amort_prog", 0) + h.get("abono_extra", 0))) for h in p.get("historial_pagos", []) if get_dt(h.get("fecha")) and (get_dt(h["fecha"]).year < now.year or (get_dt(h["fecha"]).year == now.year and get_dt(h["fecha"]).month <= i)))
                saldo_p_mes = max(0, saldo_p_mes - pagado_hasta_mes)
                
                if saldo_p_mes > 0:
                    cartera_mes += saldo_p_mes
                    # Si alguna cuota debió pagarse antes del fin del mes i y no se pagó
                    vencido = False
                    for cuota in p.get("cronograma", []):
                        if cuota.get("estado") == "PENDIENTE":
                            n = cuota.get("cuota", 1)
                            y_v = dt_creacion.year + (dt_creacion.month + n - 1) // 12
                            m_v = (dt_creacion.month + n - 1) % 12 + 1
                            if y_v < now.year or (y_v == now.year and m_v <= i):
                                vencido = True
                                break
                    if vencido: mora_mes += saldo_p_mes

            datos_mensuales.append({
                "mes": meses_nombres[i-1],
                "patrimonio": round(acum_capital + acum_utilidad, 2),
                "intereses": round(mes_interes, 2),
                "otros_ingresos": round(mes_otros_ing, 2),
                "mora": round((mora_mes / cartera_mes * 100) if cartera_mes > 0 else 0, 2)
            })

        # --- 2. DISTRIBUCIÓN DE ACTIVOS (Snapshot) ---
        cartera_total = sum(p.get("saldo_actual", 0) for p in prestamos_all if p.get("estado") == "ACTIVO")
        total_util_bruta = sum(p.get("total_interes_pagado", 0) for p in prestamos_all if p.get("estado") != "ANULADO") + \
                           sum(f["monto"] for f in flujos if f["tipo"] == "INGRESO") - \
                           sum(f["monto"] for f in flujos if f["tipo"] == "EGRESO")
        reserva_legal = max(0, total_util_bruta * 0.10)
        
        # Calcular boveda actual
        total_cap_social = sum((m.get("cantidad", 0) * m.get("valor_unitario", 20)) if m["tipo"] == "COMPRA" else -(abs(m.get("cantidad", 0)) * m.get("valor_unitario", 20)) for m in mov_acciones)
        cap_recup = sum(p.get("monto_pagado_capital", 0) for p in prestamos_all if p.get("estado") != "ANULADO")
        desembolsos = sum(p.get("capital_original", 0) for p in prestamos_all if p.get("estado") != "ANULADO")
        intereses_rec = sum(p.get("total_interes_pagado", 0) for p in prestamos_all if p.get("estado") != "ANULADO")
        otros_ing = sum(f["monto"] for f in flujos if f["tipo"] == "INGRESO")
        otros_egr = sum(f["monto"] for f in flujos if f["tipo"] == "EGRESO")
        boveda = (total_cap_social + intereses_rec + cap_recup + otros_ing) - (desembolsos + otros_egr)

        distribucion_activos = [
            {"name": "Cartera de Préstamos", "value": round(cartera_total, 2), "color": "#3b82f6"},
            {"name": "Efectivo en Bóveda", "value": round(max(0, boveda), 2), "color": "#10b981"},
            {"name": "Reserva Legal", "value": round(reserva_legal, 2), "color": "#f59e0b"}
        ]

        # --- 4. EMBUDO DE PRÉSTAMOS (Funnel) ---
        funnel_data = [
            {"label": "Capital Desembolsado", "valor": round(desembolsos, 2)},
            {"label": "Capital Recuperado", "valor": round(cap_recup, 2)},
            {"label": "Interes Generado", "valor": round(intereses_rec, 2)}
        ]

        return {
            "evolucion_patrimonio": datos_mensuales, # Patrimonio y Mora Trend
            "distribucion_activos": distribucion_activos,
            "mix_ingresos": datos_mensuales, # Intereses vs Otros
            "funnel_prestamos": funnel_data
        }

    @staticmethod
    async def obtener_ganancias_detalle_socio(unica_id: str, socio_id: str):
        from repositories.base_repo import reparticion_repo, socio_repo, config_repo, accion_repo
        import datetime
        from dateutil.relativedelta import relativedelta

        socio = await socio_repo.get_by_id(socio_id)
        if not socio: raise Exception("Socio no encontrado")

        # 1. Ganancias Historicas (Cierres ya realizados)
        reparticiones = await reparticion_repo.get_all({"unica_id": unica_id})
        ganancias_historicas = []
        total_historico = 0

        for rep in reparticiones:
            for detalle in rep.get("detalle_socios", []):
                if str(detalle.get("socio_id")) == socio_id:
                    monto = detalle.get("monto_utilidad", 0)
                    ganancias_historicas.append({
                        "anio": rep.get("anio"),
                        "monto": monto,
                        "tipo": "Cerrado",
                        "fecha": rep.get("fecha_registro")
                    })
                    total_historico += monto
                    break

        # 2. Ganancia Proyectada (Ciclo Actual)
        now = datetime.datetime.now()
        config = await config_repo.get_one({"unica_id": unica_id})
        mes_inicio = config.get("mes_inicio_ciclo", 1) if config else 1
        
        # Determinar el año del ciclo actual
        anio_ciclo = now.year if now.month >= mes_inicio else now.year - 1
        
        # Obtener utilidad proyectada actual del sistema
        proyeccion_actual = await ReporteService.obtener_reparticion_utilidades(unica_id, anio_ciclo)
        ganancia_proyectada_total = 0
        detalle_mensual_proyectado = []

        for det in proyeccion_actual.get("detalle_socios", []):
            if str(det.get("socio_id")) == socio_id:
                ganancia_proyectada_total = det.get("monto_utilidad", 0)
                break
        
        # Desglosar ganancia proyectada por mes (Estimación basada en utilidad acumulada)
        # Para esto necesitamos saber cuánto contribuyó cada mes a la utilidad actual
        mov_acciones = await accion_repo.get_all({"unica_id": unica_id, "socio_id": socio_id, "estado": "ACTIVO"})
        
        valor_accion_mes = proyeccion_actual["resumen"].get("valor_por_accion_mes", 0)
        
        def get_dt(val):
            if isinstance(val, (datetime.datetime, datetime.date)): return val
            try: return datetime.datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            except: return None

        fecha_inicio_ciclo = datetime.datetime(anio_ciclo, mes_inicio, 1)
        
        # Calculamos cuánto dinero "generó" el socio mes a mes en este ciclo
        for i in range(12):
            mes_dt = fecha_inicio_ciclo + relativedelta(months=i)
            if mes_dt > now: break
            
            # ¿Cuatnas acciones tenía el socio que trabajaron este mes?
            # En el algoritmo Acciones-Mes, si una acción se compró en el Mes 1, trabaja 11 meses.
            # Aquí lo mostramos como "ganancia mensual devengada"
            acciones_que_trabajaron_este_mes = 0
            for m in mov_acciones:
                dt_m = get_dt(m.get("fecha"))
                if not dt_m: continue
                # Si se compró antes o durante este mes, contribuye a la utilidad del ciclo
                # Pero en la repartición, el peso depende de cuántos meses faltan para el cierre.
                # Simplificación para la vista: ganancia_mes = (acciones_sistema) * valor_accion_mes
                if dt_m <= mes_dt:
                    acciones_que_trabajaron_este_mes += m.get("cantidad", 0)
            
            detalle_mensual_proyectado.append({
                "mes": mes_dt.strftime("%b %Y"),
                "acciones": acciones_que_trabajaron_este_mes,
                "ganancia_estimada": round(acciones_que_trabajaron_este_mes * valor_accion_mes, 2)
            })

        return {
            "socio": {
                "nombres": f"{socio['nombres']} {socio['apellidos']}",
                "dni": socio["dni"]
            },
            "total_ganado_historico": round(total_historico, 2),
            "ganancia_proyectada_ciclo": round(ganancia_proyectada_total, 2),
            "total_acumulado": round(total_historico + ganancia_proyectada_total, 2),
            "historial_cierres": ganancias_historicas,
            "proyeccion_mensual": detalle_mensual_proyectado
        }
