from pydantic import BaseModel
from datetime import datetime

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
class PagoBase(BaseModel):
    vecino_id: int
    cuota: str
    importe: float
    estado: str = "pendiente"
    metodo_pago: str = "no_asignado"
    recibo_asociado: str | None = None


class PagoCreate(PagoBase):
    pass


class PagoUpdate(BaseModel):
    cuota: str | None = None
    importe: float | None = None
    estado: str | None = None
    metodo_pago: str | None = None
    recibo_asociado: str | None = None


class PagoResponse(PagoBase):
    id: int
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    class Config:
        from_attributes = True

class CuotaBase(BaseModel):
    tipo: str
    descripcion: str | None = None
    importe: float
    estado: str = "programada"
    fecha_emision: datetime | None = None
    fecha_cierre: datetime | None = None


class CuotaCreate(CuotaBase):
    pass


class CuotaUpdate(BaseModel):
    tipo: str | None = None
    descripcion: str | None = None
    importe: float | None = None
    estado: str | None = None
    fecha_emision: datetime | None = None
    fecha_cierre: datetime | None = None


class CuotaResponse(CuotaBase):
    id: int
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    class Config:
        from_attributes = True
