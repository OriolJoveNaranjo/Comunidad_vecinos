from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/incidencias",
    tags=["Incidencias"]
)


@router.post("/", response_model=schemas.IncidenciaResponse)
def crear_incidencia(incidencia: schemas.IncidenciaCreate, db: Session = Depends(get_db)):
    vecino = db.query(models.Vecino).filter(models.Vecino.id == incidencia.vecino_id).first()
    if not vecino:
        raise HTTPException(status_code=404, detail="Vecino no encontrado")

    nueva_incidencia = models.Incidencia(**incidencia.dict())
    db.add(nueva_incidencia)
    db.commit()
    db.refresh(nueva_incidencia)
    return nueva_incidencia


@router.get("/", response_model=list[schemas.IncidenciaResponse])
def listar_incidencias(db: Session = Depends(get_db)):
    return db.query(models.Incidencia).all()


@router.get("/vecino/{vecino_id}", response_model=list[schemas.IncidenciaResponse])
def listar_incidencias_por_vecino(vecino_id: int, db: Session = Depends(get_db)):
    return db.query(models.Incidencia).filter(models.Incidencia.vecino_id == vecino_id).all()


@router.get("/{incidencia_id}", response_model=schemas.IncidenciaResponse)
def obtener_incidencia(incidencia_id: int, db: Session = Depends(get_db)):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia


@router.put("/{incidencia_id}", response_model=schemas.IncidenciaResponse)
def actualizar_incidencia(incidencia_id: int, datos: schemas.IncidenciaUpdate, db: Session = Depends(get_db)):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(incidencia, campo, valor)

    db.commit()
    db.refresh(incidencia)
    return incidencia


@router.delete("/{incidencia_id}")
def eliminar_incidencia(incidencia_id: int, db: Session = Depends(get_db)):
    incidencia = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    db.delete(incidencia)
    db.commit()
    return {"mensaje": "Incidencia eliminada correctamente"}
