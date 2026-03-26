from repositories.base_repo import accion_repo, socio_repo, config_repo, prestamo_repo, caja_repo
from bson import ObjectId

class RankingService:
    
    @staticmethod
    async def generar_ranking_acciones(unica_id: str):
        # 1. Obtener socios y configuración
        socios = await socio_repo.get_all({"unica_id": unica_id})
        config = await config_repo.get_one({"unica_id": unica_id})
        valor_accion = config.get("valor_accion", 20.0) if config else 20.0
        
        # 2. Obtener movimientos de acciones ACTIVOS
        movimientos = await accion_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        
        # 3. Calcular Utilidad Total del Banco para repartir
        # Intereses de préstamos (Lo que realmente ha ganado el banco)
        todos_prestamos = await prestamo_repo.get_all({"unica_id": unica_id})
        total_intereses_ganados = sum(p.get("total_interes_pagado", 0) for p in todos_prestamos)
        
        # Flujos de caja (Multas, donaciones, menos gastos operativos)
        flujos_caja = await caja_repo.get_all({"unica_id": unica_id, "estado": "ACTIVO"})
        ingresos_extra = sum(f["monto"] for f in flujos_caja if f["tipo"] == "INGRESO")
        egresos_operativos = sum(f["monto"] for f in flujos_caja if f["tipo"] == "EGRESO")
        
        utilidad_repartible = max(0, (total_intereses_ganados + ingresos_extra) - egresos_operativos)
        
        # 4. Consolidar acciones por socio
        ranking = {str(s["_id"]): {"socio": s, "total_acciones": 0, "monto_acumulado": 0.0} for s in socios}
        total_acciones_banco = 0
        
        for m in movimientos:
            s_id = str(m.get("socio_id"))
            if s_id in ranking:
                cant = m.get("cantidad", 0)
                ranking[s_id]["total_acciones"] += cant
                total_acciones_banco += cant
        
        # 5. Calcular rentabilidad
        utilidad_por_accion = utilidad_repartible / total_acciones_banco if total_acciones_banco > 0 else 0
        
        resultados = []
        for key, value in ranking.items():
            value["monto_acumulado"] = round(value["total_acciones"] * valor_accion, 2)
            value["utilidad_estimada"] = round(value["total_acciones"] * utilidad_por_accion, 2)
            
            # Rentabilidad porcentual sobre el capital invertido
            if value["monto_acumulado"] > 0:
                value["rentabilidad_porc"] = round((value["utilidad_estimada"] / value["monto_acumulado"]) * 100, 2)
            else:
                value["rentabilidad_porc"] = 0.0
                
            s = value["socio"]
            value["nombres"] = f"{s['nombres']} {s['apellidos']}"
            del value["socio"]
            resultados.append(value)
            
        resultados.sort(key=lambda x: x["total_acciones"], reverse=True)
        return resultados
