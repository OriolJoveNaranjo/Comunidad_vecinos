from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db


router = APIRouter(
    prefix="/morosidad",
    tags=["Morosidad"],
)


def calcular_deudas(
    db: Session,
    vecino_id: int | None = None,
):
    hoy = date.today()

    totales = (
        db.query(
            models.Pago.cuota_vecino_id.label("asignacion_id"),
            func.sum(models.Pago.importe).label("pagado"),
        )
        .group_by(models.Pago.cuota_vecino_id)
        .subquery()
    )

    pagado = func.coalesce(totales.c.pagado, Decimal("0.00"))
    pendiente = models.CuotaVecino.importe - pagado

    consulta = (
        db.query(
            models.CuotaVecino,
            models.Cuota,
            models.Vecino,
            pagado.label("pagado"),
            pendiente.label("pendiente"),
        )
        .join(
            models.Cuota,
            models.Cuota.id == models.CuotaVecino.cuota_id,
        )
        .join(
            models.Vecino,
            models.Vecino.id == models.CuotaVecino.vecino_id,
        )
        .outerjoin(
            totales,
            totales.c.asignacion_id == models.CuotaVecino.id,
        )
        .filter(
            models.Cuota.fecha_vencimiento < hoy,
            pendiente > 0,
        )
    )

    if vecino_id is not None:
        consulta = consulta.filter(
            models.CuotaVecino.vecino_id == vecino_id
        )

    filas = consulta.order_by(
        models.Cuota.fecha_vencimiento,
        models.CuotaVecino.id,
    ).all()

    return [
        schemas.DeudaVencidaResponse(
            cuota_vecino_id=asignacion.id,
            cuota_id=cuota.id,
            vecino_id=vecino.id,
            nombre=vecino.nombre,
            apellido=vecino.apellido,
            piso=vecino.piso,
            puerta=vecino.puerta,
            concepto=cuota.concepto,
            fecha_vencimiento=cuota.fecha_vencimiento,
            dias_atraso=(hoy - cuota.fecha_vencimiento).days,
            importe=asignacion.importe,
            pagado=suma_pagada,
            pendiente=saldo_pendiente,
        )
        for (
            asignacion,
            cuota,
            vecino,
            suma_pagada,
            saldo_pendiente,
        ) in filas
    ]


@router.get(
    "/deudas",
    response_model=list[schemas.DeudaVencidaResponse],
)
def listar_deudas_vencidas(
    vecino_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return calcular_deudas(db, vecino_id)


@router.get(
    "/vecinos",
    response_model=list[schemas.MorosidadVecinoResponse],
)
def resumir_morosidad_por_vecino(
    vecino_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    deudas = calcular_deudas(db, vecino_id)
    resumen = {}

    for deuda in deudas:
        if deuda.vecino_id not in resumen:
            resumen[deuda.vecino_id] = (
                schemas.MorosidadVecinoResponse(
                    vecino_id=deuda.vecino_id,
                    nombre=deuda.nombre,
                    apellido=deuda.apellido,
                    piso=deuda.piso,
                    puerta=deuda.puerta,
                    cuotas_vencidas=0,
                    deuda_vencida=Decimal("0.00"),
                    vencimiento_mas_antiguo=deuda.fecha_vencimiento,
                    dias_atraso_maximo=0,
                )
            )

        vecino = resumen[deuda.vecino_id]
        vecino.cuotas_vencidas += 1
        vecino.deuda_vencida += deuda.pendiente
        vecino.vencimiento_mas_antiguo = min(
            vecino.vencimiento_mas_antiguo,
            deuda.fecha_vencimiento,
        )
        vecino.dias_atraso_maximo = max(
            vecino.dias_atraso_maximo,
            deuda.dias_atraso,
        )

    return sorted(
        resumen.values(),
        key=lambda vecino: (
            -vecino.deuda_vencida,
            vecino.vecino_id,
        ),
    )