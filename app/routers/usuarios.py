from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.core.dependencies import requerir_superadmin, requerir_admin
from app.core.security import hash_password


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],    
)


@router.post(
    "/",
    response_model=schemas.UsuarioResponse,
    status_code=201,
)
def crear_usuario(
    datos: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    administrador: models.Usuario = Depends(requerir_admin),
):
    if administrador.rol == "admin" and datos.rol != "vecino":
        raise HTTPException(
            403,
            "Un administrador solo puede crear cuentas de vecinos",
        )

    email = datos.email.strip().lower()

    

    if (
        email.count("@") != 1
        or any(caracter.isspace() for caracter in email)
    ):
        raise HTTPException(422, "Email inválido")

    parte_local, dominio = email.split("@")

    if not parte_local or not dominio:
        raise HTTPException(422, "Email inválido")

    if datos.rol == "vecino" and datos.vecino_id is None:
        raise HTTPException(
            422,
            "Un usuario vecino debe estar asociado a un vecino",
        )

    existente = db.query(models.Usuario.id).filter(
        func.lower(models.Usuario.email) == email
    ).first()

    if existente:
        raise HTTPException(409, "El email ya está registrado")

    if datos.vecino_id is not None:
        vecino = db.query(models.Vecino).filter(
            models.Vecino.id == datos.vecino_id
        ).first()

        if vecino is None:
            raise HTTPException(404, "Vecino no encontrado")

        if not vecino.activo:
            raise HTTPException(
                409,
                "No se puede crear una cuenta para un vecino inactivo",
            )

        cuenta_existente = db.query(models.Usuario.id).filter(
            models.Usuario.vecino_id == datos.vecino_id
        ).first()

        if cuenta_existente:
            raise HTTPException(
                409,
                "Este vecino ya tiene una cuenta de usuario",
            )

    usuario = models.Usuario(
        email=email,
        password_hash=hash_password(datos.password),
        rol=datos.rol,
        vecino_id=datos.vecino_id,
        activo=True,
    )

    db.add(usuario)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        codigo = getattr(error.orig, "sqlstate", None)

        if codigo == "23505":
            raise HTTPException(
                409,
                "El email o el vecino ya tienen una cuenta registrada",
            ) from error

        if codigo == "23503":
            raise HTTPException(
                409,
                "El vecino asociado ya no está disponible",
            ) from error

        raise

    db.refresh(usuario)
    return usuario


@router.get(
    "/",
    response_model=list[schemas.UsuarioResponse],
    dependencies=[Depends(requerir_admin)],
)
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).order_by(
        models.Usuario.id
    ).all()
@router.patch(
    "/{usuario_id}/rol",
    response_model=schemas.UsuarioResponse,
     dependencies=[Depends(requerir_superadmin)],
)
def cambiar_rol(
    usuario_id: int,
    datos: schemas.UsuarioRolUpdate,
    db: Session = Depends(get_db),
    superadmin: models.Usuario = Depends(requerir_superadmin),
):
    # Serializa los cambios para proteger al último superadmin.
    db.execute(
        text(
            "LOCK TABLE usuarios "
            "IN SHARE ROW EXCLUSIVE MODE"
        )
    )

    # Comprueba de nuevo los permisos tras obtener el bloqueo.
    db.refresh(superadmin)

    if not superadmin.activo or superadmin.rol != "superadmin":
        raise HTTPException(
            403,
            "Esta acción requiere permisos de superadministrador",
        )

    usuario = (
        db.query(models.Usuario)
        .populate_existing()
        .filter(models.Usuario.id == usuario_id)
        .first()
    )

    if usuario is None:
        raise HTTPException(404, "Usuario no encontrado")

    if usuario.rol == datos.rol:
        return usuario

    if datos.rol == "vecino" and usuario.vecino_id is None:
        raise HTTPException(
            409,
            "El usuario debe estar asociado a un vecino "
            "antes de asignarle ese rol",
        )

    if (
        usuario.rol == "superadmin"
        and usuario.activo
        and datos.rol != "superadmin"
    ):
        total_superadmins = db.query(models.Usuario).filter(
            models.Usuario.rol == "superadmin",
            models.Usuario.activo.is_(True),
        ).count()

        if total_superadmins <= 1:
            raise HTTPException(
                409,
                "No se puede quitar el rol al último "
                "superadmin activo",
            )

    cambio = models.CambioRol(
        usuario_id=usuario.id,
        realizado_por_id=superadmin.id,
        rol_anterior=usuario.rol,
        rol_nuevo=datos.rol,
    )

    usuario.rol = datos.rol
    db.add(cambio)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(usuario)
    return usuario


@router.get(
    "/cambios-rol",
    response_model=list[schemas.CambioRolResponse],
)
def listar_cambios_rol(db: Session = Depends(get_db)):
    return db.query(models.CambioRol).order_by(
        models.CambioRol.id.desc()
    ).all()