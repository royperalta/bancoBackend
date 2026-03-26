from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_admin
from models.schemas import PrestamoCreate, PagoCuotaRequest
from services.prestamo_service import PrestamoService
from repositories.base_repo import prestamo_repo

router = APIRouter(prefix="/api/prestamos", tags=["Préstamos"])

@router.post("")
async def crear_prestamo(data: PrestamoCreate, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if data.unica_id != unica_id and current_user["rol"] != "SUPERADMIN":
        raise HTTPException(403, "No autorizado para esta UNICA")
    
    return await PrestamoService.crear_prestamo(data.socio_id, data.unica_id, data.capital_original, data.meses_originales)

@router.get("/vigentes")
async def obtener_prestamos_vigentes(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await PrestamoService.listar_vigentes(unica_id)

@router.post("/{prestamo_id}/pagar/{cuota}")
async def pagar_cuota(prestamo_id: str, cuota: int, data: PagoCuotaRequest, current_user: dict = Depends(get_current_admin)):
    return await PrestamoService.registrar_pago(prestamo_id, cuota, data.monto_pagado)

@router.post("/{prestamo_id}/anular")
async def anular_prestamo(prestamo_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    motivo = data.get("motivo", "Anulado por el administrador")
    return await PrestamoService.anular_prestamo(prestamo_id, motivo)

@router.get("/reporte")
async def reporte_prestamos(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await PrestamoService.obtener_reporte_completo(unica_id)

@router.put("/{prestamo_id}")
async def actualizar_prestamo(prestamo_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    # Solo administradores pueden editar préstamos directamente
    return await PrestamoService.actualizar_prestamo(prestamo_id, data)

@router.delete("/{prestamo_id}")
async def eliminar_prestamo(prestamo_id: str, current_user: dict = Depends(get_current_admin)):
    prestamo = await prestamo_repo.get_by_id(prestamo_id)
    if not prestamo: raise HTTPException(404, "Préstamo no encontrado")
    
    if prestamo.get("monto_pagado_capital", 0) > 0:
        raise HTTPException(400, "No se puede eliminar un préstamo con pagos registrados")
        
    await prestamo_repo.delete(prestamo_id)
    return {"message": "Préstamo eliminado"}
