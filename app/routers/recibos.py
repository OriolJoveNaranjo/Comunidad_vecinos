from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.responses import Response
from app.services.recibos_pdf import generar_recibo_pdf

from app import models, schemas
from app.database import get_db


router = APIRouter(
    prefix="/recibos",
    tags=["Recibos"],
)


@router.post(
    "/",
    response_model=schemas.ReciboResponse,
    status_code=201,
)
def emitir_recibo(
    datos: schemas.ReciboCreate,
    db: Session = Depends(get_db),
):
    pago = db.query(models.Pago).filter(
        models.Pago.id == datos.pago_id
    ).first()

    if pago is None:
        raise HTTPException(404, "Pago no encontrado")

    # Usamos el mismo bloqueo que al modificar o eliminar pagos.
    asignacion = (
        db.query(models.CuotaVecino)
        .filter(models.CuotaVecino.id == pago.cuota_vecino_id)
        .with_for_update()
        .first()
    )

    if asignacion is None:
        raise HTTPException(404, "Asignación de cuota no encontrada")

    # Recargamos el pago después de obtener el bloqueo.
    pago = (
        db.query(models.Pago)
        .populate_existing()
        .filter(models.Pago.id == datos.pago_id)
        .first()
    )

    if pago is None:
        raise HTTPException(404, "Pago no encontrado")

    existente = db.query(models.Recibo.id).filter(
        models.Recibo.pago_id == pago.id
    ).first()

    if existente or pago.recibo_asociado:
        raise HTTPException(
            409,
            "Este pago ya tiene un recibo asociado",
        )

    vecino = asignacion.vecino
    cuota = asignacion.cuota
    ahora = datetime.now(timezone.utc)
    numero = f"REC-{ahora.year}-{pago.id:08d}"

    recibo = models.Recibo(
        numero=numero,
        pago_id=pago.id,
        nombre=vecino.nombre,
        apellido=vecino.apellido,
        piso=vecino.piso,
        puerta=vecino.puerta,
        concepto=cuota.concepto,
        importe=pago.importe,
        fecha_pago=pago.fecha_pago,
        metodo_pago=pago.metodo_pago,
        fecha_emision=ahora,
    )

    db.add(recibo)
    pago.recibo_asociado = numero

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                409,
                "Ya existe un recibo para este pago o con este número",
            ) from error

        raise

    db.refresh(recibo)
    return recibo


@router.get(
    "/",
    response_model=list[schemas.ReciboResponse],
)
def listar_recibos(
    pago_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Recibo)

    if pago_id is not None:
        consulta = consulta.filter(
            models.Recibo.pago_id == pago_id
        )

    return consulta.order_by(models.Recibo.id.desc()).all()


@router.get(
    "/{recibo_id}",
    response_model=schemas.ReciboResponse,
)
def obtener_recibo(
    recibo_id: int,
    db: Session = Depends(get_db),
):
    recibo = db.query(models.Recibo).filter(
        models.Recibo.id == recibo_id
    ).first()

    if recibo is None:
        raise HTTPException(404, "Recibo no encontrado")

    return recibo
@router.get(
    "/{recibo_id}/pdf",
    response_class=Response,
    responses={
        200: {
            "description": "Justificante de pago en PDF",
            "content": {"application/pdf": {}},
        },
    },
)
def descargar_recibo_pdf(
    recibo_id: int,
    db: Session = Depends(get_db),
):
    recibo = obtener_recibo(recibo_id, db)
    contenido = generar_recibo_pdf(recibo)

    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{recibo.numero}.pdf"'
            ),
        },
    )