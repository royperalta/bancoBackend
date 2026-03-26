import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)

database = client.get_database("unicas") if "unicas" in MONGO_URL else client.unica_banco

def get_collection(name: str):
    return database.get_collection(name)
