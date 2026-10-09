from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


Importe = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=2),
]

TipoCuota = Literal["mensual", "extraordinaria", "derrama"]
MetodoPago = Literal["transferencia", "efectivo", "domiciliacion"]

# Esquema base (comparten campos comunes)
class VecinoBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    telefono: str | None = None
    piso: str
    puerta: str
    activo: bool = True

# Para crear un vecino (no incluye id ni timestamps)
class VecinoCreate(VecinoBase):
    pass

# Para actualizar un vecino (todos opcionales)
class VecinoUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    email: str | None = None
    telefono: str | None = None
    piso: str | None = None
    puerta: str | None = None
    activo: bool | None = None

# Para devolver un vecino (incluye id y fechas)
class VecinoResponse(VecinoBase):
    id: int
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    class Config:
        from_attributes = True
class IncidenciaBase(BaseModel):
    titulo: str
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"
    vecino_id: int


class IncidenciaCreate(IncidenciaBase):
    pass


class IncidenciaUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    estado: str | None = None
    prioridad: str | None = None


class IncidenciaResponse(IncidenciaBase):
    id: int
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    class Config:
        from_attributes = True
        
class CuotaCreate(BaseModel):
    concepto: str = Field(min_length=1, max_length=150)
    tipo: TipoCuota
    descripcion: str | None = None
    importe: Importe
    fecha_vencimiento: date


class CuotaUpdate(BaseModel):
    concepto: str = Field(min_length=1, max_length=150)
    tipo: TipoCuota
    descripcion: str | None = None
    importe: Importe
    fecha_vencimiento: date


class CuotaResponse(CuotaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: Literal["programada", "emitida", "cerrada"]
    fecha_emision: datetime | None = None
    fecha_cierre: datetime | None = None
    creado_en: datetime
    actualizado_en: datetime | None = None


class CuotaEmitir(BaseModel):
    # None: emitir para todos los vecinos activos.
    # Una lista: emitir únicamente para esos vecinos.
    vecino_ids: list[int] | None = Field(default=None, min_length=1)


class CuotaVecinoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cuota_id: int
    vecino_id: int
    importe: Decimal
    creado_en: datetime


class SaldoCuotaResponse(BaseModel):
    cuota_vecino_id: int
    cuota_id: int
    vecino_id: int
    concepto: str
    fecha_vencimiento: date
    importe: Decimal
    pagado: Decimal
    pendiente: Decimal
    estado: Literal["pendiente", "parcial", "pagada", "atrasada"]


class PagoCreate(BaseModel):
    cuota_vecino_id: int = Field(gt=0)
    importe: Importe
    fecha_pago: date
    metodo_pago: MetodoPago
    observaciones: str | None = None


class PagoUpdate(BaseModel):
    importe: Importe
    fecha_pago: date
    metodo_pago: MetodoPago
    observaciones: str | None = None


class PagoResponse(PagoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recibo_asociado: str | None = None
    creado_en: datetime
    actualizado_en: datetime | None = None

class DeudaVencidaResponse(BaseModel):
    cuota_vecino_id: int
    cuota_id: int
    vecino_id: int
    nombre: str
    apellido: str
    piso: str
    puerta: str
    concepto: str
    fecha_vencimiento: date
    dias_atraso: int
    importe: Decimal
    pagado: Decimal
    pendiente: Decimal


class MorosidadVecinoResponse(BaseModel):
    vecino_id: int
    nombre: str
    apellido: str
    piso: str
    puerta: str
    cuotas_vencidas: int
    deuda_vencida: Decimal
    vencimiento_mas_antiguo: date
    dias_atraso_maximo: int