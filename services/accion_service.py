from repositories.base_repo import accion_repo, config_repo, socio_repo
from core.exceptions import BusinessError
from bson import ObjectId
from datetime import datetime

class AccionService:
    @staticmethod
    async def registrar_movimiento(unica_id: str, socio_id: str, cantidad: int, tipo: str, motivo: str):
        config = await config_repo.get_one({"unica_id": unica_id})
        valor_unitario = config.get("valor_accion", 20.0) if config else 20.0
        
        movimiento = {
            "unica_id": unica_id,
            "socio_id": socio_id,
            "cantidad": cantidad,
            "valor_unitario": valor_unitario,
            "tipo": tipo,
            "motivo": motivo,
            "fecha": datetime.now(),
            "estado": "ACTIVO"
        }
        return await accion_repo.create(movimiento)

    @staticmethod
    async def editar_movimiento(movimiento_id: str, cantidad: int, motivo: str):
        mov = await accion_repo.get_by_id(movimiento_id)
        if not mov: raise BusinessError("Movimiento no encontrado")
        
        update_data = {
            "cantidad": cantidad,
            "motivo": f"{motivo} (Editado el {datetime.now().strftime('%Y-%m-%d %H:%M')})",
            "fecha_edicion": datetime.now()
        }
        return await accion_repo.update({"_id": ObjectId(movimiento_id)}, update_data)

    @staticmethod
    async def anular_movimiento(movimiento_id: str, motivo_anulacion: str):
        mov = await accion_repo.get_by_id(movimiento_id)
        if not mov: raise BusinessError("Movimiento no encontrado")
        
        update_data = {
            "estado": "ANULADO",
            "motivo_anulacion": motivo_anulacion,
            "fecha_edicion": datetime.now() # O fecha_anulacion
        }
        return await accion_repo.update({"_id": ObjectId(movimiento_id)}, update_data)

    @staticmethod
    async def listar_historial(unica_id: str):
        movimientos = await accion_repo.get_all({"unica_id": unica_id})
        for m in movimientos:
            socio = await socio_repo.get_by_id(m["socio_id"])
            m["socio_nombre"] = f"{socio['nombres']} {socio['apellidos']}" if socio else "Socio Desconocido"
        
        # Ordenar por fecha desc
        movimientos.sort(key=lambda x: x.get("fecha", datetime.min), reverse=True)
        return movimientos
