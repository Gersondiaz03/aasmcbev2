from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Any

from app.core.deps import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.models.roles import Role
from app.services.users import UserService
from app.core.security import get_password_hash, verify_password

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(
        nombre=user_in.nombre,
        apellido=user_in.apellido,
        email=user_in.email,
        contrasena=get_password_hash(user_in.contrasena),  # Hash password
        id_rol=user_in.id_rol,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id_usuario == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id_usuario == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return Response(status_code=204)


@router.post("/init-users", tags=["Init"])
async def create_default_users(db: AsyncSession = Depends(get_db)):
    # Utilidad para buscar rol por nombre
    async def get_role_id(nombre_rol):
        result = await db.execute(select(Role).where(Role.nombre_rol == nombre_rol))
        role = result.scalar_one_or_none()
        if not role:
            raise Exception(f"Role '{nombre_rol}' not found")
        return role.id_rol

    usuarios = [
        {
            "nombre": "admin",
            "apellido": "admin",
            "email": "admin@admin.com",
            "contrasena": get_password_hash("admin"),
            "id_rol": await get_role_id("ADMINISTRADOR"),
        },
        {
            "nombre": "estudiante",
            "apellido": "estudiante",
            "email": "estudiante@estudiante.com",
            "contrasena": get_password_hash("estudiante"),
            "id_rol": await get_role_id("ESTUDIANTE"),
        },
        {
            "nombre": "psicologo",
            "apellido": "psicologo",
            "email": "psicologo@psicologo.com",
            "contrasena": get_password_hash("psicologo"),
            "id_rol": await get_role_id("PSICOLOGO"),
        },
    ]

    results = []
    for u in usuarios:
        user = await UserService.get_by_email(db, u["email"])
        if not user:
            user = await UserService.create(db, UserCreate(**u))
            results.append({"email": user.email, "id_usuario": user.id_usuario})
        else:
            results.append(
                {
                    "email": user.email,
                    "id_usuario": user.id_usuario,
                    "msg": "Ya existía",
                }
            )
    return results


@router.put("/{user_id}/password", status_code=204)
async def update_password(
    user_id: int,
    new_password: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id_usuario == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.contrasena = get_password_hash(new_password)
    db.add(user)
    await db.commit()
    return Response(status_code=204)


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    user_update: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id_usuario == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Only update provided fields
    for field, value in user_update.items():
        if hasattr(user, field):
            if field == "contrasena":
                setattr(user, field, get_password_hash(value))
            else:
                setattr(user, field, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/change-password", status_code=204)
async def change_password(
    email: str = Body(...),
    current_password: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(current_password, user.contrasena):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    user.contrasena = get_password_hash(new_password)
    db.add(user)
    await db.commit()
    return Response(status_code=204)
