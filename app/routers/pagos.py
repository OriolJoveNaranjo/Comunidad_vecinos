from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"]
)

# Crear pago
@router.post("/", response_model=schemas.PagoResponse)
def crear_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    vecino = db.query(models.Vecino).filter(models.Vecino.id == pago.vecino_id).first()
    if not vecino:
        raise HTTPException(status_code=404, detail="Vecino no encontrado")

    nuevo_pago = models.Pago(**pago.dict())
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago


# Listar todos los pagos
@router.get("/", response_model=list[schemas.PagoResponse])
def listar_pagos(db: Session = Depends(get_db)):
    return db.query(models.Pago).all()


# Listar pagos por vecino
@router.get("/vecino/{vecino_id}", response_model=list[schemas.PagoResponse])
def pagos_por_vecino(vecino_id: int, db: Session = Depends(get_db)):
    return db.query(models.Pago).filter(models.Pago.vecino_id == vecino_id).all()


# Obtener pago por ID
@router.get("/{pago_id}", response_model=schemas.PagoResponse)
def obtener_pago(pago_id: int, db: Session = Depends(get_db)):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


# Actualizar pago
@router.put("/{pago_id}", response_model=schemas.PagoResponse)
def actualizar_pago(pago_id: int, datos: schemas.PagoUpdate, db: Session = Depends(get_db)):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(pago, campo, valor)

    db.commit()
    db.refresh(pago)
    return pago


# Eliminar pago
@router.delete("/{pago_id}")
def eliminar_pago(pago_id: int, db: Session = Depends(get_db)):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    db.delete(pago)
    db.commit()
    return {"mensaje": "Pago eliminado correctamente"}
