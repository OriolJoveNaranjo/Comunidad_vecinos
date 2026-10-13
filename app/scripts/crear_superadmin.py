from getpass import getpass

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Usuario
from app.core.security import hash_password


def main():
    email = input("Email del superadmin: ").strip().lower()

    if (
        len(email) > 254
        or email.count("@") != 1
        or any(caracter.isspace() for caracter in email)
    ):
        print("Introduce un email válido.")
        return

    parte_local, dominio = email.split("@")

    if not parte_local or not dominio:
        print("Introduce un email válido.")
        return

    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmacion = getpass("Repite la contraseña: ")

    if not 12 <= len(password) <= 128:
        print("La contraseña debe tener entre 12 y 128 caracteres.")
        return

    if password != confirmacion:
        print("Las contraseñas no coinciden.")
        return

    password_hash = hash_password(password)

    with Session(engine) as db:
        try:
            # Evita ejecutar dos creaciones iniciales a la vez.
            db.execute(
                text(
                    "LOCK TABLE usuarios "
                    "IN SHARE ROW EXCLUSIVE MODE"
                )
            )

            existente = db.query(Usuario.id).filter(
                Usuario.rol == "superadmin"
            ).first()

            if existente:
                print(
                    "Ya existe un superadmin. "
                    "Este comando solo crea el primero."
                )
                return

            email_existente = db.query(Usuario.id).filter(
                func.lower(Usuario.email) == email
            ).first()

            if email_existente:
                print("Ese email ya pertenece a un usuario.")
                return

            usuario = Usuario(
                email=email,
                password_hash=password_hash,
                rol="superadmin",
                activo=True,
                vecino_id=None,
            )

            db.add(usuario)
            db.commit()
            db.refresh(usuario)

            print(
                f"Superadmin creado correctamente. ID: {usuario.id}"
            )

        except IntegrityError:
            db.rollback()
            print(
                "No se pudo crear el superadmin "
                "por un conflicto en la base de datos."
            )


if __name__ == "__main__":
    main()