from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_admin
from repositories.base_repo import transaccion_repo
from models.schemas import TransaccionBase

router = APIRouter(prefix="/api/transacciones", tags=["Transacciones Mensuales"])

@router.get("/{anio}/{mes}")
async def listar_transacciones_mes(anio: int, mes: int, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: return []
    return await transaccion_repo.get_all({"unica_id": unica_id, "mes": mes, "anio": anio})

@router.post("")
async def registrar_transaccion(data: dict, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    # Clean data and ensure unique compound check (one transaction per socio per month)
    id_socio = data.get("id_socio")
    mes = data.get("mes")
    anio = data.get("anio")
    
    if not id_socio or not mes or not anio:
        raise HTTPException(400, "Faltan campos obligatorios (id_socio, mes, anio)")
    
    query = {"unica_id": unica_id, "id_socio": id_socio, "mes": mes, "anio": anio}
    exists = await transaccion_repo.get_one(query)
    
    doc = {
        "unica_id": unica_id,
        "id_socio": id_socio,
        "mes": mes,
        "anio": anio,
        "deposito_ahorros": data.get("deposito_ahorros", 0),
        "retiro_ahorros": data.get("retiro_ahorros", 0),
        "numero_acciones": data.get("numero_acciones", 0),
        "pagos_capital": data.get("pagos_capital", 0),
        "intereses_recibidos": data.get("intereses_recibidos", 0),
        "prestamos_otorgados": data.get("prestamos_otorgados", 0),
        "interes_pagado": data.get("interes_pagado", 0)
    }

    if exists:
        return await transaccion_repo.update(query, doc)
    else:
        return await transaccion_repo.create(doc)
