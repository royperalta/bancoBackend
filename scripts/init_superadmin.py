import asyncio
import os
import sys

# To allow importing core modules when running as a detached script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import client, database
from core.auth import get_password_hash
from datetime import datetime

async def init_superadmin():
    usuarios_coll = database.get_collection("usuarios")
    
    pwd = "@System64.com"
    email = "superadmin@playglish.com"
    await usuarios_coll.delete_many({"rol": "SUPERADMIN"}) # Clean ALL old ones
    doc = {
        "email": email.lower(),
        "password_hash": get_password_hash(pwd),
        "rol": "SUPERADMIN",
        "unica_id": None,
        "fecha_creacion": datetime.now()
    }
    
    await usuarios_coll.insert_one(doc)
    print("=== SUPERADMIN CREADO EXITOSAMENTE ===")
    print(f"Email: {doc['email']}")
    print(f"Password: {pwd}")
    print("Por favor, guarda esta contraseña. Solo el superadmin puede crear UNICAs.")

if __name__ == "__main__":
    asyncio.run(init_superadmin())
