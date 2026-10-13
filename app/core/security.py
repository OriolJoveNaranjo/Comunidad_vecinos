import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash


SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 64:
    raise RuntimeError(
        "Configura JWT_SECRET_KEY con una clave aleatoria "
        "de al menos 64 caracteres antes de arrancar"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def crear_access_token(usuario_id: int) -> str:
    ahora = datetime.now(timezone.utc)

    contenido = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        contenido,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def obtener_usuario_id_del_token(token: str) -> int:
    error_credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o sesión caducada",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        contenido = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )

        identificador = contenido["sub"]

        if not isinstance(identificador, str):
            raise error_credenciales

        usuario_id = int(identificador)

        if usuario_id <= 0:
            raise error_credenciales

        return usuario_id

    except (InvalidTokenError, ValueError, TypeError):
        raise error_credenciales from None