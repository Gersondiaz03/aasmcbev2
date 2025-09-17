from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models.roles import Role
from app.schemas.roles import RoleCreate, RoleRead

router = APIRouter()


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(role_in: RoleCreate, db: AsyncSession = Depends(get_db)):
    db_role = Role(nombre_rol=role_in.nombre_rol)
    db.add(db_role)
    await db.commit()
    await db.refresh(db_role)
    return db_role


@router.get("/", response_model=list[RoleRead])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).where(Role.id_rol == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}", status_code=204)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).where(Role.id_rol == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    await db.delete(role)
    await db.commit()
