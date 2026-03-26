from motor.motor_asyncio import AsyncIOMotorClient
from core.database import get_collection
from bson import ObjectId

class BaseRepository:
    def __init__(self, collection_name: str):
        self.collection = get_collection(collection_name)

    async def get_all(self, query: dict = None):
        if query is None: query = {}
        items = []
        async for doc in self.collection.find(query):
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return items

    async def get_by_id(self, id: str):
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        if doc: doc["_id"] = str(doc["_id"])
        return doc

    async def get_one(self, query: dict):
        doc = await self.collection.find_one(query)
        if doc: doc["_id"] = str(doc["_id"])
        return doc

    async def create(self, data: dict):
        res = await self.collection.insert_one(data)
        data["_id"] = str(res.inserted_id)
        return data

    async def update(self, query: dict, data: dict, upsert: bool = False):
        await self.collection.update_one(query, {"$set": data}, upsert=upsert)
        return await self.get_one(query)

    async def delete(self, id: str):
        await self.collection.delete_one({"_id": ObjectId(id)})

# Singleton instances
unica_repo = BaseRepository("unicas")
usuario_repo = BaseRepository("usuarios")
config_repo = BaseRepository("configuracion")
socio_repo = BaseRepository("socios")
transaccion_repo = BaseRepository("transacciones")
prestamo_repo = BaseRepository("prestamos")
pago_prestamo_repo = BaseRepository("pagos_prestamo")
caja_repo = BaseRepository("caja_flujo")
accion_repo = BaseRepository("acciones_movimientos")
reparticion_repo = BaseRepository("reparticion_utilidades")
