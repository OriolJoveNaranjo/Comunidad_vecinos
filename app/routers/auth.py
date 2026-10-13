from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.core.dependencies import obtener_usuario_actual
from app.core.security import (
    crear_access_token,
    hash_password,
    verificar_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

# Permite comprobar una contraseña incluso si el email no existe.
HASH_FICTICIO = hash_password("ClaveFicticiaSinCuenta123!")


@router.post("/token", response_model=schemas.TokenResponse)
def iniciar_sesion(
    formulario: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = formulario.username.strip().lower()

    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == email
    ).first()

    hash_guardado = (
        usuario.password_hash
        if usuario is not None
        else HASH_FICTICIO
    )

    password_correcta = verificar_password(
        formulario.password,
        hash_guardado,
    )

    if (
        usuario is None
        or not password_correcta
        or not usuario.activo
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return schemas.TokenResponse(
        access_token=crear_access_token(usuario.id),
    )


@router.get("/me", response_model=schemas.UsuarioResponse)
def consultar_mi_usuario(
    usuario: models.Usuario = Depends(obtener_usuario_actual),
):
    return usuario