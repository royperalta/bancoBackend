from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_admin
from models.schemas import CajaFlujoCreate
from repositories.base_repo import caja_repo
from datetime import datetime

router = APIRouter(prefix="/api/caja", tags=["Flujo de Caja Directo"])

@router.post("")
async def registrar_flujo_caja(data: CajaFlujoCreate, current_user: dict = Depends(get_current_admin)):
    doc = data.model_dump()
    if data.unica_id != current_user.get("unica_id") and current_user.get("rol") != "SUPERADMIN":
        raise HTTPException(403, "No autorizado")
        
    doc["fecha"] = datetime.now()
    doc["estado"] = "ACTIVO"
    return await caja_repo.create(doc)

@router.get("")
async def resumen_mes(mes: int, anio: int, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: return []
    
    all_docs = await caja_repo.get_all({"unica_id": unica_id})
    def get_dt(val):
        if isinstance(val, datetime): return val
        try: return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except: return None

    filtrados = []
    for d in all_docs:
        dt = get_dt(d.get("fecha"))
        if dt and dt.month == mes and dt.year == anio:
            if isinstance(d["fecha"], datetime):
                d["fecha"] = d["fecha"].isoformat()
            filtrados.append(d)
                                  
    # Solo sumar los movimientos ACTIVOS para el balance real
    ingresos = sum(d["monto"] for d in filtrados if d["tipo"] == "INGRESO" and d.get("estado") == "ACTIVO")
    egresos  = sum(d["monto"] for d in filtrados if d["tipo"] == "EGRESO" and d.get("estado") == "ACTIVO")
    
    # Ordenar historial para que los más nuevos salgan arriba
    filtrados.sort(key=lambda x: x.get("fecha"), reverse=True)

    return {
        "historial": filtrados,
        "total_ingresos": ingresos,
        "total_egresos": egresos,
        "balance": ingresos - egresos
    }

from bson import ObjectId

@router.delete("/{flujo_id}")
async def eliminar_flujo(flujo_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    exists = await caja_repo.get_by_id(flujo_id)
    if not exists or (exists.get("unica_id") != current_user.get("unica_id") and current_user.get("rol") != "SUPERADMIN"):
        raise HTTPException(403, "No autorizado")
    
    motivo = data.get("motivo", "Anulación manual")
    update_data = {
        "estado": "ANULADO",
        "motivo_anulacion": motivo,
        "fecha_edicion": datetime.now()
    }
    await caja_repo.update({"_id": ObjectId(flujo_id)}, update_data)
    return {"message": "Movimiento anulado correctamente"}

@router.put("/{flujo_id}")
async def actualizar_flujo(flujo_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    exists = await caja_repo.get_by_id(flujo_id)
    if not exists or (exists.get("unica_id") != current_user.get("unica_id") and current_user.get("rol") != "SUPERADMIN"):
        raise HTTPException(403, "No autorizado")
    
    data["fecha_edicion"] = datetime.now()
    if "motivo_edicion" not in data:
        data["motivo_edicion"] = "Edición administrativa"
        
    return await caja_repo.update({"_id": ObjectId(flujo_id)}, data)
