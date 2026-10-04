from fastapi import FastAPI
from app.database import Base, engine

app = FastAPI(title="Gestión Comunidad de Vecinos")

# Crear tablas automáticamente (solo para pruebas)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}