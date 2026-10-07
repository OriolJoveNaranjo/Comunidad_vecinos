from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Vecino(Base):
    __tablename__ = "vecinos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=True)
    piso = Column(String, nullable=False)
    puerta = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    incidencias = relationship("Incidencia", back_populates="vecino")

class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)

    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)

    estado = Column(String, default="pendiente")  # pendiente, en_progreso, resuelta
    prioridad = Column(String, default="media")   # baja, media, alta

    vecino_id = Column(Integer, ForeignKey("vecinos.id"), nullable=False)
    vecino = relationship("Vecino", back_populates="incidencias")

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)

    vecino_id = Column(Integer, ForeignKey("vecinos.id"), nullable=False)
    vecino = relationship("Vecino")

    cuota = Column(String, nullable=False)  # Ej: "Cuota mensual Octubre"
    importe = Column(Float, nullable=False)

    estado = Column(String, default="pendiente")  
    # estados: pendiente, pagado, atrasado

    metodo_pago = Column(String, default="no_asignado")
    # Ej: transferencia, efectivo, domiciliación

    recibo_asociado = Column(String, nullable=True)  
    # ruta o nombre del recibo PDF

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    
class Cuota(Base):
    __tablename__ = "cuotas"

    id = Column(Integer, primary_key=True, index=True)

    tipo = Column(String, nullable=False)  
    # Ej: mensual, extraordinaria, derrama

    descripcion = Column(String, nullable=True)

    importe = Column(Float, nullable=False)

    estado = Column(String, default="programada")
    # estados: programada, emitida, cerrada

    fecha_emision = Column(DateTime(timezone=True), nullable=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

