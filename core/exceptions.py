from fastapi import Request
from fastapi.responses import JSONResponse

class BusinessError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.status_code},
    )

async def uncaught_error_handler(request: Request, exc: Exception):
    print(exc) # Log for the server
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "code": 500},
    )
