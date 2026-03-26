from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from core.auth import decode_access_token
from repositories.base_repo import usuario_repo

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    user_id = payload.get("sub")
    user = await usuario_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

async def get_current_superadmin(user: dict = Depends(get_current_user)):
    if user.get("rol") != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Permisos de SUPERADMIN requeridos")
    return user

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get("rol") not in ["SUPERADMIN", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Permisos de ADMIN requeridos")
    return user
