from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(
    prefix="/vecinos",
    tags=["Vecinos"],
)


def guardar_cambios(db: Session):
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        es_email_duplicado = (
            getattr(error.orig, "sqlstate", None) == "23505"
            and getattr(
                getattr(error.orig, "diag", None),
                "constraint_name",
                None,
            ) == "vecinos_email_key"
        )

        if es_email_duplicado:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un vecino con este email",
            ) from error

        raise


# Crear vecino
@router.post("/", response_model=schemas.VecinoResponse)
def crear_vecino(
    vecino: schemas.VecinoCreate,
    db: Session = Depends(get_db),
):
    nuevo_vecino = models.Vecino(**vecino.model_dump())
    db.add(nuevo_vecino)

    guardar_cambios(db)

    db.refresh(nuevo_vecino)
    return nuevo_vecino


# Listar vecinos
@router.get("/", response_model=list[schemas.VecinoResponse])
def listar_vecinos(db: Session = Depends(get_db)):
    return db.query(models.Vecino).all()


# Obtener vecino por ID
@router.get("/{vecino_id}", response_model=schemas.VecinoResponse)
def obtener_vecino(
    vecino_id: int,
    db: Session = Depends(get_db),
):
    vecino = (
        db.query(models.Vecino)
        .filter(models.Vecino.id == vecino_id)
        .first()
    )

    if vecino is None:
        raise HTTPException(
            status_code=404,
            detail="Vecino no encontrado",
        )

    return vecino


# Actualizar vecino
@router.put("/{vecino_id}", response_model=schemas.VecinoResponse)
def actualizar_vecino(
    vecino_id: int,
    datos: schemas.VecinoUpdate,
    db: Session = Depends(get_db),
):
    vecino = obtener_vecino(vecino_id, db)

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(vecino, campo, valor)

    guardar_cambios(db)

    db.refresh(vecino)
    return vecino


# Eliminar vecino
@router.delete("/{vecino_id}")
def eliminar_vecino(
    vecino_id: int,
    db: Session = Depends(get_db),
):
    vecino = obtener_vecino(vecino_id, db)

    db.delete(vecino)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if getattr(error.orig, "sqlstate", None) == "23503":
            raise HTTPException(
                status_code=409,
                detail=(
                    "No se puede eliminar el vecino porque tiene "
                    "registros asociados"
                ),
            ) from error

        raise

    return {"mensaje": "Vecino eliminado correctamente"}