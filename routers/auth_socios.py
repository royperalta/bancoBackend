from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_admin, get_current_superadmin, get_current_user
from models.schemas import UnicaCreate, UsuarioCreate, SocioCreate, Configuracion
from repositories.base_repo import unica_repo, usuario_repo, socio_repo, config_repo, prestamo_repo
from core.auth import verify_password, create_access_token, get_password_hash
from datetime import datetime
from bson import ObjectId

router = APIRouter(tags=["Auth y Usuarios"])

@router.post("/api/auth/login")
async def login(data: dict):
    email = data.get("email", "").strip().lower()
    password = data.get("password")
    
    user = await usuario_repo.get_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
         raise HTTPException(status_code=401, detail="Credenciales incorrectas")
         
    token = create_access_token({"sub": str(user["_id"]), "rol": user["rol"], "unica_id": user.get("unica_id")})
    return {"access_token": token, "rol": user["rol"], "unica_id": user.get("unica_id")}

# - SUPERADMIN OPS
@router.post("/api/unicas")
async def create_unica(data: UnicaCreate, current_user: dict = Depends(get_current_superadmin)):
    doc = data.model_dump()
    doc["fecha_creacion"] = datetime.now()
    doc["estado"] = "Activa"
    res = await unica_repo.create(doc)
    
    await config_repo.create({
        "unica_id": str(res["_id"]),
        "valor_accion": 20.0,
        "porcentaje_ganancia_accion": 3.0,
        "porcentaje_interes_prestamo": 3.0
    })
    return {"message": "UNICA creada", "unica": res}

@router.get("/api/unicas")
async def list_unicas(current_user: dict = Depends(get_current_superadmin)):
    return await unica_repo.get_all()

@router.get("/api/reportes/global")
async def reportes_globales(current_user: dict = Depends(get_current_superadmin)):
    total_unicas = len(await unica_repo.get_all())
    total_socios = len(await socio_repo.get_all())
    # You could calculate global capital here summing from Caja in the future
    return {
        "total_unicas": total_unicas,
        "total_socios": total_socios
    }

@router.post("/api/usuarios/admin")
async def create_admin(data: UsuarioCreate, current_user: dict = Depends(get_current_superadmin)):
    from core.exceptions import BusinessError
    exists = await usuario_repo.get_one({"email": data.email.lower()})
    if exists:
        raise BusinessError("El usuario ya existe", status_code=400)
    
    doc = data.model_dump()
    doc["email"] = data.email.lower()
    doc["password_hash"] = get_password_hash(data.password)
    del doc["password"]
    doc["fecha_creacion"] = datetime.now()
    
    res = await usuario_repo.create(doc)
    return {"message": "Admin creado", "user": res}

# - ADMIN OPS
@router.get("/api/socios")
async def list_socios(current_user: dict = Depends(get_current_admin)):
    return await socio_repo.get_all({"unica_id": current_user.get("unica_id")})

@router.post("/api/socios")
async def crear_socio(data: SocioCreate, current_user: dict = Depends(get_current_admin)):
    doc = data.model_dump()
    doc["fecha_ingreso"] = datetime.now()
    if data.unica_id != current_user.get("unica_id") and current_user.get("rol") != "SUPERADMIN":
        raise HTTPException(403, "No puedes crear socios en otra UNICA")
    
    return await socio_repo.create(doc)

@router.delete("/api/socios/{socio_id}")
async def eliminar_socio(socio_id: str, current_user: dict = Depends(get_current_admin)):
     # Verificar si tiene deuda pendiente
     deuda = await prestamo_repo.get_one({"socio_id": socio_id, "saldo_actual": {"$gt": 0}})
     if deuda:
          raise HTTPException(status_code=400, detail="No se puede eliminar el socio porque tiene deudas pendientes")
          
     await socio_repo.delete(socio_id)
     return {"message": "Socio eliminado"}

@router.put("/api/socios/{socio_id}")
async def editar_socio(socio_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    # Validate it belongs to same unica
    exists = await socio_repo.get_by_id(socio_id)
    if not exists or (exists.get("unica_id") != current_user.get("unica_id") and current_user.get("rol") != "SUPERADMIN"):
        raise HTTPException(403, "No autorizado")
    
    return await socio_repo.update({"_id": ObjectId(socio_id)}, data)

@router.get("/api/configuracion")
async def get_config(current_user: dict = Depends(get_current_admin)):
    return await config_repo.get_one({"unica_id": current_user.get("unica_id")})

@router.post("/api/configuracion")
async def registrar_config(data: Configuracion, current_user: dict = Depends(get_current_admin)):
    exists = await config_repo.get_one({"unica_id": data.unica_id})
    payload = data.model_dump()
    if exists:
        # Usar ObjectId para asegurar que el update funcione en Mongo
        return await config_repo.update({"_id": ObjectId(exists["_id"])}, payload)
    return await config_repo.create(payload)

import shutil
import os
from fastapi import UploadFile, File

@router.post("/api/configuracion/upload-logo")
async def upload_logo(file: UploadFile = File(...), current_user: dict = Depends(get_current_admin)):
    unica_id = current_user.get("unica_id")
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    file_ext = file.filename.split(".")[-1]
    file_name = f"logo_{unica_id}.{file_ext}"
    file_path = os.path.join("uploads", file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Devolver la URL relativa
    return {"logo_url": f"/uploads/{file_name}"}
