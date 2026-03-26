from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# --- UNICA ---
class UnicaCreate(BaseModel):
    nombre: str

class Unica(UnicaCreate):
    id: str = Field(alias="_id")
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    estado: str = "Activa"

# --- USUARIO ---
class UsuarioSocioCreate(BaseModel):
    nombres: str
    apellidos: str
    dni: str
    sexo: str
    fecha_nacimiento: str

class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str
    rol: str = "ADMIN"
    unica_id: Optional[str] = None
    socio_data: Optional[UsuarioSocioCreate] = None

class Usuario(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    password_hash: str
    rol: str
    unica_id: Optional[str] = None
    socio_id: Optional[str] = None

# --- CONFIGURACION ---
class Configuracion(BaseModel):
    unica_id: str
    valor_accion: float = 20.0
    porcentaje_ganancia_accion: float = 3.0
    porcentaje_interes_prestamo: float = 3.0
    mes_inicio_ciclo: int = 1 # 1 = Enero, 6 = Junio, etc.
    # Branding
    nombre_banco: Optional[str] = "Mi UNICA"
    logo_url: Optional[str] = None
    color_primario: Optional[str] = "#3b82f6" # Default blue-500
    color_paleta: Optional[str] = "blue"

# --- SOCIO ---
class SocioBase(BaseModel):
    unica_id: str
    nombres: str
    apellidos: str
    dni: str
    sexo: str
    fecha_nacimiento: str
    celular: Optional[str] = None
    direccion: Optional[str] = None
    email: Optional[str] = None
    estado: str = "Activo"

class SocioCreate(SocioBase):
    pass

class Socio(SocioBase):
    id: str = Field(alias="_id")
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    usuario_id: Optional[str] = None

# --- PRESTAMOS ---
class PrestamoCreate(BaseModel):
    unica_id: str
    socio_id: str
    capital_original: float
    # El interes se trae de la configuracion
    meses_originales: int

class Prestamo(PrestamoCreate):
    id: str = Field(alias="_id")
    tasa_mensual: float
    tipo_calculo: str = "saldo_decreciente"
    saldo_actual: float
    monto_pagado_capital: float = 0.0
    total_interes_pagado: float = 0.0
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    estado: str = "ACTIVO" # ACTIVO | CANCELADO
    cronograma: list = []
    historial_pagos: list = []

class PagoPrestamo(BaseModel):
    prestamo_id: str
    unica_id: str
    socio_id: str
    monto_pago: float # Esto deduce capital e interes
    capital_amortizado: float
    interes_pagado: float
    mes: int
    anio: int
    fecha_pago: datetime = Field(default_factory=datetime.now)

# --- CAJA DIRECTA ---
class CajaFlujoCreate(BaseModel):
    unica_id: str
    tipo: str # "INGRESO" | "EGRESO"
    categoria: str # "Reserva Legal", "Gastos Admin", "Multa", "Otros"
    monto: float
    descripcion: str
    fecha: datetime = Field(default_factory=datetime.now)
    estado: str = "ACTIVO" # ACTIVO, ANULADO
    fecha_edicion: Optional[datetime] = None
    motivo_anulacion: Optional[str] = None
    motivo_edicion: Optional[str] = None

# --- TRANSACCIONES MENSUALES ---
class TransaccionBase(BaseModel):
    unica_id: str
    mes: int
    anio: int
    id_socio: str
    deposito_ahorros: float = 0.0
    retiro_ahorros: float = 0.0
    numero_acciones_compradas: int = 0

class PagoCuotaRequest(BaseModel):
    monto_pagado: float

# --- ACCIONES ---
class AccionMovimientoCreate(BaseModel):
    socio_id: str
    cantidad: int # Puede ser positivo o negativo
    tipo: str = "COMPRA" # COMPRA, VENTA, AJUSTE
    motivo: Optional[str] = None

class AccionMovimiento(AccionMovimientoCreate):
    id: str = Field(alias="_id")
    unica_id: str
    valor_unitario: float
    fecha: datetime = Field(default_factory=datetime.now)
    fecha_edicion: Optional[datetime] = None
    estado: str = "ACTIVO" # ACTIVO, ANULADO
    motivo_anulacion: Optional[str] = None

# --- REPARTICION DE UTILIDADES ---
class SocioReparticion(BaseModel):
    socio_id: str
    nombres: str
    dni: str
    acciones_al_cierre: int
    acciones_mes_acumuladas: float = 0.0 # Acciones prorrateadas por el tiempo
    porcentaje_participacion: float
    monto_utilidad: float

class ReparticionUtilidades(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    unica_id: str
    anio: int
    fecha_registro: datetime = Field(default_factory=datetime.now)
    total_interes_prestamos: float
    otros_ingresos: float
    otros_gastos: float
    utilidad_bruta: float
    gastos_acumulados: float = 0.0
    utilidad_neta: float = 0.0
    reserva_legal_10: float
    utilidad_distribuible: float
    total_acciones_sistema: int
    total_acciones_mes_sistema: float = 0.0
    valor_por_accion: float
    valor_por_accion_mes: float = 0.0
    detalle_socios: List[SocioReparticion]

# --- NUEVOS SCHEMAS PARA UTILIDADES ---
class CapitalizarUtilidadRequest(BaseModel):
    socio_id: str
    monto_utilidad: float
    anio: int

class CobrarDeudaUtilidadRequest(BaseModel):
    socio_id: str
    monto_utilidad: float
    anio: int
