from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.core.security import obtener_usuario_id_del_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
)


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    usuario_id = obtener_usuario_id_del_token(token)

    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id
    ).first()

    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o usuario desactivado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def requerir_admin(
    usuario: models.Usuario = Depends(obtener_usuario_actual),
):
    if usuario.rol not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de administrador",
        )

    return usuario


def requerir_superadmin(
    usuario: models.Usuario = Depends(obtener_usuario_actual),
):
    if usuario.rol != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta acción requiere permisos de superadministrador",
        )

    return usuario