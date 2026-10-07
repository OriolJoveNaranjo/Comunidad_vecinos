from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/cuotas",
    tags=["Cuotas"]
)

# Crear cuota
@router.post("/", response_model=schemas.CuotaResponse)
def crear_cuota(cuota: schemas.CuotaCreate, db: Session = Depends(get_db)):
    nueva_cuota = models.Cuota(**cuota.dict())
    db.add(nueva_cuota)
    db.commit()
    db.refresh(nueva_cuota)
    return nueva_cuota


# Listar cuotas
@router.get("/", response_model=list[schemas.CuotaResponse])
def listar_cuotas(db: Session = Depends(get_db)):
    return db.query(models.Cuota).all()


# Obtener cuota por ID
@router.get("/{cuota_id}", response_model=schemas.CuotaResponse)
def obtener_cuota(cuota_id: int, db: Session = Depends(get_db)):
    cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    return cuota


# Actualizar cuota
@router.put("/{cuota_id}", response_model=schemas.CuotaResponse)
def actualizar_cuota(cuota_id: int, datos: schemas.CuotaUpdate, db: Session = Depends(get_db)):
    cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(cuota, campo, valor)

    db.commit()
    db.refresh(cuota)
    return cuota


# Eliminar cuota
@router.delete("/{cuota_id}")
def eliminar_cuota(cuota_id: int, db: Session = Depends(get_db)):
    cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")

    db.delete(cuota)
    db.commit()
    return {"mensaje": "Cuota eliminada correctamente"}
