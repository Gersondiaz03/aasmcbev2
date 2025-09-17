from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.roles import Role


class RoleService:
    @staticmethod
    async def get_all(db: AsyncSession):
        result = await db.execute(select(Role))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, role_id: int):
        result = await db.execute(select(Role).where(Role.id_rol == role_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, nombre_rol: str):
        db_role = Role(nombre_rol=nombre_rol)
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        return db_role

    @staticmethod
    async def delete(db: AsyncSession, role_id: int):
        role = await RoleService.get_by_id(db, role_id)
        if role:
            await db.delete(role)
            await db.commit()
        return role
