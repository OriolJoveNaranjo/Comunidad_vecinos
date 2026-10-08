from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db


router = APIRouter(prefix="/pagos", tags=["Pagos"])


def buscar_asignacion(db: Session, asignacion_id: int):
    asignacion = (
        db.query(models.CuotaVecino)
        .filter(models.CuotaVecino.id == asignacion_id)
        .with_for_update()
        .first()
    )

    if asignacion is None:
        raise HTTPException(404, "Asignación de cuota no encontrada")

    return asignacion


def total_pagado(
    db: Session,
    asignacion_id: int,
    excluir_pago_id: int | None = None,
):
    consulta = db.query(func.sum(models.Pago.importe)).filter(
        models.Pago.cuota_vecino_id == asignacion_id
    )

    if excluir_pago_id is not None:
        consulta = consulta.filter(
            models.Pago.id != excluir_pago_id
        )

    return consulta.scalar() or Decimal("0.00")


def comprobar_importe(
    db: Session,
    asignacion: models.CuotaVecino,
    importe: Decimal,
    excluir_pago_id: int | None = None,
):
    pagado = total_pagado(
        db,
        asignacion.id,
        excluir_pago_id,
    )
    pendiente = asignacion.importe - pagado

    if importe > pendiente:
        raise HTTPException(
            409,
            f"El importe supera el saldo pendiente de {pendiente:.2f} €",
        )


@router.post(
    "/",
    response_model=schemas.PagoResponse,
    status_code=201,
)
def crear_pago(
    datos: schemas.PagoCreate,
    db: Session = Depends(get_db),
):
    asignacion = buscar_asignacion(db, datos.cuota_vecino_id)
    comprobar_importe(db, asignacion, datos.importe)

    pago = models.Pago(**datos.model_dump())
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


@router.get("/", response_model=list[schemas.PagoResponse])
def listar_pagos(
    cuota_vecino_id: int | None = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Pago)

    if cuota_vecino_id is not None:
        consulta = consulta.filter(
            models.Pago.cuota_vecino_id == cuota_vecino_id
        )

    return consulta.order_by(models.Pago.id.desc()).all()


# Esta ruta debe aparecer antes de /{pago_id}.
@router.get(
    "/saldos",
    response_model=list[schemas.SaldoCuotaResponse],
)
def consultar_saldos(
    vecino_id: int | None = None,
    db: Session = Depends(get_db),
):
    totales = (
        db.query(
            models.Pago.cuota_vecino_id.label("asignacion_id"),
            func.sum(models.Pago.importe).label("pagado"),
        )
        .group_by(models.Pago.cuota_vecino_id)
        .subquery()
    )

    consulta = (
        db.query(
            models.CuotaVecino,
            models.Cuota,
            totales.c.pagado,
        )
        .join(
            models.Cuota,
            models.Cuota.id == models.CuotaVecino.cuota_id,
        )
        .outerjoin(
            totales,
            totales.c.asignacion_id == models.CuotaVecino.id,
        )
    )

    if vecino_id is not None:
        consulta = consulta.filter(
            models.CuotaVecino.vecino_id == vecino_id
        )

    filas = consulta.order_by(models.CuotaVecino.id).all()
    resultados = []

    for asignacion, cuota, suma_pagada in filas:
        pagado = suma_pagada or Decimal("0.00")
        pendiente = asignacion.importe - pagado

        if pendiente <= 0:
            estado = "pagada"
        elif cuota.fecha_vencimiento < date.today():
            estado = "atrasada"
        elif pagado > 0:
            estado = "parcial"
        else:
            estado = "pendiente"

        resultados.append(
            schemas.SaldoCuotaResponse(
                cuota_vecino_id=asignacion.id,
                cuota_id=cuota.id,
                vecino_id=asignacion.vecino_id,
                concepto=cuota.concepto,
                fecha_vencimiento=cuota.fecha_vencimiento,
                importe=asignacion.importe,
                pagado=pagado,
                pendiente=pendiente,
                estado=estado,
            )
        )

    return resultados


@router.get(
    "/{pago_id}",
    response_model=schemas.PagoResponse,
)
def obtener_pago(
    pago_id: int,
    db: Session = Depends(get_db),
):
    pago = db.query(models.Pago).filter(
        models.Pago.id == pago_id
    ).first()

    if pago is None:
        raise HTTPException(404, "Pago no encontrado")

    return pago


@router.put(
    "/{pago_id}",
    response_model=schemas.PagoResponse,
)
def actualizar_pago(
    pago_id: int,
    datos: schemas.PagoUpdate,
    db: Session = Depends(get_db),
):
    pago = obtener_pago(pago_id, db)
    asignacion = buscar_asignacion(db, pago.cuota_vecino_id)

    # Recarga el pago después de bloquear su asignación.
    db.refresh(pago)

    if pago.recibo_asociado:
        raise HTTPException(
            409,
            "No se puede modificar un pago con recibo asociado",
        )

    comprobar_importe(
        db,
        asignacion,
        datos.importe,
        excluir_pago_id=pago.id,
    )

    for campo, valor in datos.model_dump().items():
        setattr(pago, campo, valor)

    db.commit()
    db.refresh(pago)
    return pago


@router.delete("/{pago_id}")
def eliminar_pago(
    pago_id: int,
    db: Session = Depends(get_db),
):
    pago = obtener_pago(pago_id, db)
    buscar_asignacion(db, pago.cuota_vecino_id)
    db.refresh(pago)

    if pago.recibo_asociado:
        raise HTTPException(
            409,
            "No se puede eliminar un pago con recibo asociado",
        )

    db.delete(pago)
    db.commit()
    return {"mensaje": "Pago eliminado correctamente"}