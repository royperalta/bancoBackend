from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from core.security import get_current_admin
from services.reporte_service import ReporteService
from services.ranking_service import RankingService
from models.schemas import ReparticionUtilidades, CapitalizarUtilidadRequest, CobrarDeudaUtilidadRequest

router = APIRouter(prefix="/api/reportes", tags=["Reportes y Balance"])

@router.get("/dashboard")
async def dashboard_metrics(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await ReporteService.obtener_metricas_dashboard(unica_id)

@router.get("/ranking")
async def get_ranking(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await RankingService.generar_ranking_acciones(unica_id)

@router.get("/balance/{anio}/{mes}")
async def monthly_balance(anio: int, mes: int, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await ReporteService.obtener_balance_mensual(unica_id, mes, anio)

@router.get("/reparticion")
async def profit_distribution(anio: Optional[int] = None, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    import datetime
    target_year = anio or datetime.datetime.now().year
    return await ReporteService.obtener_reparticion_utilidades(unica_id, target_year)

@router.post("/reparticion/confirmar")
async def confirm_profit_distribution(data: ReparticionUtilidades, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    data.unica_id = unica_id
    try:
        return await ReporteService.registrar_reparticion(data.model_dump())
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/reparticion/capitalizar")
async def capitalize_profit(data: CapitalizarUtilidadRequest, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    try:
        return await ReporteService.capitalizar_utilidad(unica_id, data.socio_id, data.monto_utilidad, data.anio)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/reparticion/cobrar-deuda")
async def pay_debt_with_profit(data: CobrarDeudaUtilidadRequest, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    try:
        return await ReporteService.cobrar_deuda_con_utilidad(unica_id, data.socio_id, data.monto_utilidad, data.anio)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/reparticion/historial")
async def historical_profit_distribution(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await ReporteService.listar_reparticiones_historicas(unica_id)

@router.get("/salud")
async def financial_health(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await ReporteService.obtener_indicadores_salud(unica_id)

@router.get("/analitica")
async def advanced_analytics(current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    return await ReporteService.obtener_analitica_avanzada(unica_id)

@router.get("/ganancias-socio/{socio_id}")
async def get_socio_earnings(socio_id: str, current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not unica_id: raise HTTPException(400, "Necesitas estar en una UNICA")
    try:
        return await ReporteService.obtener_ganancias_detalle_socio(unica_id, socio_id)
    except Exception as e:
        raise HTTPException(400, str(e))
