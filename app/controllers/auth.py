from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models.users import User
from app.schemas.users import LoginRequest
from app.utils.auth import create_access_token, verify_password

router = APIRouter()


@router.post("/login")
async def login(form_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not verify_password(form_data.password, user.contrasena):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Obtener el nombre del rol del usuario (si tienes la relación con Roles)
    rol_nombre = None
    if hasattr(user, "rol") and hasattr(user.rol, "nombre_rol"):
        rol_nombre = user.rol.nombre_rol
    elif hasattr(user, "id_rol"):
        # Realiza una consulta para obtener el nombre del rol si es necesario
        from app.models.roles import Role

        result = await db.execute(select(Role).where(Role.id_rol == user.id_rol))
        rol = result.scalar_one_or_none()
        rol_nombre = rol.nombre_rol if rol else None

    access_token = create_access_token(data={"sub": str(user.id_usuario)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id_usuario": user.id_usuario,
            "email": user.email,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "rol": rol_nombre,
        },
    }
