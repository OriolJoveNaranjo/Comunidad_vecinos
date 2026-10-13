from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import auth, usuarios, vecinos, incidencias, pagos, cuotas, morosidad, recibos

# Crear tablas automáticamente
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestión Comunidad de Vecinos")

@app.get("/")
def root():
    return {"message": "Backend funcionando correctamente"}

# Registrar router
app.include_router(vecinos.router)
app.include_router(incidencias.router)
app.include_router(pagos.router)
app.include_router(cuotas.router)
app.include_router(morosidad.router)
app.include_router(recibos.router)
app.include_router(auth.router)
app.include_router(usuarios.router)