from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.exceptions import BusinessError, business_error_handler, uncaught_error_handler
from routers import auth_socios, prestamos, caja

app = FastAPI(
    title="UNICA Banco API V3",
    description="Sistema Transaccional de Minibancos con Clean Architecture Multi-Tenant",
    version="3.0.0"
)

# Callbacks Errores Globales
app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(Exception, uncaught_error_handler)

# CORS Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Asegurar que el directorio de uploads existe
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Registro de routers modulares
app.include_router(auth_socios.router)
app.include_router(prestamos.router)
app.include_router(caja.router)
from routers import acciones, reportes, importador
app.include_router(acciones.router)
app.include_router(reportes.router)
app.include_router(importador.router)

# Servir archivos estáticos para logos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def health_check():
    return {"status": "ok", "version": "3.0.0"}
