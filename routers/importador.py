from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.importador_service import ImportadorService
from core.exceptions import BusinessError

router = APIRouter(prefix="/api/importador", tags=["Importador"])

@router.post("/excel")
async def importar_excel(
    unica_id: str = Form(...),
    anio: int = Form(...),
    archivo: UploadFile = File(...)
):
    if not archivo.filename.endswith(('.xls', '.xlsx')):
        raise BusinessError("El archivo debe ser un Excel (.xlsx o .xls)")
        
    try:
        resultado = await ImportadorService.importar_excel_du(unica_id, anio, archivo)
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise BusinessError(f"Error procesando el archivo Excel: {str(e)}")

@router.post("/reset")
async def reset_data(
    unica_id: str = Form(...)
):
    try:
        from repositories.base_repo import socio_repo, accion_repo, prestamo_repo, caja_repo, reparticion_repo, pago_prestamo_repo
        
        # Eliminar data operativa de la UNICA
        query = {"unica_id": unica_id}
        
        await socio_repo.collection.delete_many(query)
        await accion_repo.collection.delete_many(query)
        await prestamo_repo.collection.delete_many(query)
        await caja_repo.collection.delete_many(query)
        await reparticion_repo.collection.delete_many(query)
        await pago_prestamo_repo.collection.delete_many(query)
        
        return {"status": "success", "message": "Toda la data operativa de la UNICA ha sido eliminada."}
    except Exception as e:
        raise BusinessError(f"Error al resetear la data: {str(e)}")
