from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    ForeignKey, Numeric, UniqueConstraint, CheckConstraint,
)
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
    estado = Column(String, default="pendiente")
    prioridad = Column(String, default="media")

    vecino_id = Column(Integer, ForeignKey("vecinos.id"), nullable=False)
    vecino = relationship("Vecino", back_populates="incidencias")

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class Cuota(Base):
    __tablename__ = "cuotas"

    __table_args__ = (
        CheckConstraint("importe > 0", name="ck_cuota_importe_positivo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    concepto = Column(String(150), nullable=False)
    tipo = Column(String(30), nullable=False)
    descripcion = Column(String, nullable=True)
    importe = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="programada")

    fecha_vencimiento = Column(Date, nullable=False)
    fecha_emision = Column(DateTime(timezone=True), nullable=True)
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)

    creado_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    asignaciones = relationship(
        "CuotaVecino",
        back_populates="cuota",
        passive_deletes="all",
    )


class CuotaVecino(Base):
    __tablename__ = "cuotas_vecinos"

    __table_args__ = (
        UniqueConstraint("cuota_id", "vecino_id", name="uq_cuota_vecino"),
        CheckConstraint(
            "importe > 0",
            name="ck_cuota_vecino_importe_positivo",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    cuota_id = Column(
        Integer,
        ForeignKey("cuotas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vecino_id = Column(
        Integer,
        ForeignKey("vecinos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    importe = Column(Numeric(12, 2), nullable=False)
    creado_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cuota = relationship("Cuota", back_populates="asignaciones")
    vecino = relationship("Vecino")
    pagos = relationship(
        "Pago",
        back_populates="asignacion",
        passive_deletes="all",
    )


class Pago(Base):
    __tablename__ = "pagos"

    __table_args__ = (
        CheckConstraint("importe > 0", name="ck_pago_importe_positivo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    cuota_vecino_id = Column(
        Integer,
        ForeignKey("cuotas_vecinos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    importe = Column(Numeric(12, 2), nullable=False)
    fecha_pago = Column(Date, nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    observaciones = Column(String, nullable=True)
    recibo_asociado = Column(String, nullable=True)

    creado_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    asignacion = relationship("CuotaVecino", back_populates="pagos")
class Recibo(Base):
    __tablename__ = "recibos"

    __table_args__ = (
        CheckConstraint(
            "importe > 0",
            name="ck_recibo_importe_positivo",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), unique=True, nullable=False)

    pago_id = Column(
        Integer,
        ForeignKey("pagos.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )

    # Copia de los datos en el momento de emitir el recibo.
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    piso = Column(String, nullable=False)
    puerta = Column(String, nullable=False)
    concepto = Column(String(150), nullable=False)
    importe = Column(Numeric(12, 2), nullable=False)
    fecha_pago = Column(Date, nullable=False)
    metodo_pago = Column(String(30), nullable=False)

    fecha_emision = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    pago = relationship("Pago")