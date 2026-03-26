from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_admin
from services.ranking_service import RankingService
from services.accion_service import AccionService
from models.schemas import AccionMovimientoCreate

router = APIRouter(prefix="/api/acciones", tags=["Acciones y Ranking"])

@router.get("/ranking")
async def obtener_ranking(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: return []
    return await RankingService.generar_ranking_acciones(unica_id)

@router.get("/movimientos")
async def obtener_historial_acciones(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await AccionService.listar_historial(unica_id)

@router.post("/movimientos")
async def registrar_movimiento(data: AccionMovimientoCreate, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    return await AccionService.registrar_movimiento(
        unica_id, data.socio_id, data.cantidad, data.tipo, data.motivo
    )

@router.put("/movimientos/{mov_id}")
async def editar_movimiento(mov_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    return await AccionService.editar_movimiento(mov_id, data.get("cantidad"), data.get("motivo"))

@router.post("/movimientos/{mov_id}/anular")
async def anular_movimiento(mov_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    return await AccionService.anular_movimiento(mov_id, data.get("motivo_anulacion"))
