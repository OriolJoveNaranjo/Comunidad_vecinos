from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/vecinos",
    tags=["Vecinos"]
)

# Crear vecino
@router.post("/", response_model=schemas.VecinoResponse)
def crear_vecino(vecino: schemas.VecinoCreate, db: Session = Depends(get_db)):
    nuevo_vecino = models.Vecino(**vecino.dict())
    db.add(nuevo_vecino)
    db.commit()
    db.refresh(nuevo_vecino)
    return nuevo_vecino

# Listar vecinos
@router.get("/", response_model=list[schemas.VecinoResponse])
def listar_vecinos(db: Session = Depends(get_db)):
    return db.query(models.Vecino).all()

# Obtener vecino por ID
@router.get("/{vecino_id}", response_model=schemas.VecinoResponse)
def obtener_vecino(vecino_id: int, db: Session = Depends(get_db)):
    vecino = db.query(models.Vecino).filter(models.Vecino.id == vecino_id).first()
    if not vecino:
        raise HTTPException(status_code=404, detail="Vecino no encontrado")
    return vecino

# Actualizar vecino
@router.put("/{vecino_id}", response_model=schemas.VecinoResponse)
def actualizar_vecino(vecino_id: int, datos: schemas.VecinoUpdate, db: Session = Depends(get_db)):
    vecino = db.query(models.Vecino).filter(models.Vecino.id == vecino_id).first()
    if not vecino:
        raise HTTPException(status_code=404, detail="Vecino no encontrado")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(vecino, campo, valor)

    db.commit()
    db.refresh(vecino)
    return vecino

# Eliminar vecino
@router.delete("/{vecino_id}")
def eliminar_vecino(vecino_id: int, db: Session = Depends(get_db)):
    vecino = db.query(models.Vecino).filter(models.Vecino.id == vecino_id).first()
    if not vecino:
        raise HTTPException(status_code=404, detail="Vecino no encontrado")

    db.delete(vecino)
    db.commit()
    return {"mensaje": "Vecino eliminado correctamente"}
