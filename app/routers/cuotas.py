from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/cuotas", tags=["Cuotas"])


def buscar_cuota(db: Session, cuota_id: int, bloquear: bool = False):
    consulta = db.query(models.Cuota).filter(
        models.Cuota.id == cuota_id
    )

    if bloquear:
        consulta = consulta.with_for_update()

    cuota = consulta.first()

    if cuota is None:
        raise HTTPException(404, "Cuota no encontrada")

    return cuota


@router.post(
    "/",
    response_model=schemas.CuotaResponse,
    status_code=201,
)
def crear_cuota(
    datos: schemas.CuotaCreate,
    db: Session = Depends(get_db),
):
    cuota = models.Cuota(**datos.model_dump())
    db.add(cuota)
    db.commit()
    db.refresh(cuota)
    return cuota


@router.get("/", response_model=list[schemas.CuotaResponse])
def listar_cuotas(db: Session = Depends(get_db)):
    return db.query(models.Cuota).order_by(
        models.Cuota.id.desc()
    ).all()


@router.get(
    "/{cuota_id}",
    response_model=schemas.CuotaResponse,
)
def obtener_cuota(
    cuota_id: int,
    db: Session = Depends(get_db),
):
    return buscar_cuota(db, cuota_id)


@router.put(
    "/{cuota_id}",
    response_model=schemas.CuotaResponse,
)
def actualizar_cuota(
    cuota_id: int,
    datos: schemas.CuotaUpdate,
    db: Session = Depends(get_db),
):
    cuota = buscar_cuota(db, cuota_id, bloquear=True)

    if cuota.estado != "programada":
        raise HTTPException(
            409,
            "Solo se pueden modificar cuotas no emitidas",
        )

    for campo, valor in datos.model_dump().items():
        setattr(cuota, campo, valor)

    db.commit()
    db.refresh(cuota)
    return cuota


@router.post(
    "/{cuota_id}/emitir",
    response_model=list[schemas.CuotaVecinoResponse],
    status_code=201,
)
def emitir_cuota(
    cuota_id: int,
    datos: schemas.CuotaEmitir,
    db: Session = Depends(get_db),
):
    cuota = buscar_cuota(db, cuota_id, bloquear=True)

    if cuota.estado != "programada":
        raise HTTPException(
            409,
            "La cuota ya está emitida o cerrada",
        )

    consulta = db.query(models.Vecino).filter(
        models.Vecino.activo.is_(True)
    )

    if datos.vecino_ids is not None:
        ids = set(datos.vecino_ids)

        vecinos = consulta.filter(
            models.Vecino.id.in_(ids)
        ).all()

        encontrados = {vecino.id for vecino in vecinos}
        faltantes = sorted(ids - encontrados)

        if faltantes:
            raise HTTPException(
                422,
                f"Vecinos inexistentes o inactivos: {faltantes}",
            )
    else:
        vecinos = consulta.all()

    if not vecinos:
        raise HTTPException(
            409,
            "No hay vecinos activos para emitir la cuota",
        )

    asignaciones = [
        models.CuotaVecino(
            cuota_id=cuota.id,
            vecino_id=vecino.id,
            importe=cuota.importe,
        )
        for vecino in vecinos
    ]

    db.add_all(asignaciones)
    cuota.estado = "emitida"
    cuota.fecha_emision = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "La cuota ya tiene asignaciones; revisa su estado",
        )

    for asignacion in asignaciones:
        db.refresh(asignacion)

    return asignaciones


@router.get(
    "/{cuota_id}/asignaciones",
    response_model=list[schemas.CuotaVecinoResponse],
)
def listar_asignaciones(
    cuota_id: int,
    db: Session = Depends(get_db),
):
    buscar_cuota(db, cuota_id)

    return db.query(models.CuotaVecino).filter(
        models.CuotaVecino.cuota_id == cuota_id
    ).order_by(models.CuotaVecino.id).all()


@router.delete("/{cuota_id}")
def eliminar_cuota(
    cuota_id: int,
    db: Session = Depends(get_db),
):
    cuota = buscar_cuota(db, cuota_id, bloquear=True)

    tiene_asignaciones = db.query(models.CuotaVecino.id).filter(
        models.CuotaVecino.cuota_id == cuota_id
    ).first()

    if cuota.estado != "programada" or tiene_asignaciones:
        raise HTTPException(
            409,
            "No se puede eliminar una cuota emitida o con asignaciones",
        )

    db.delete(cuota)
    db.commit()
    return {"mensaje": "Cuota eliminada correctamente"}