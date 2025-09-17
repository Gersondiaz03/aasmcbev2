from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import hash_password  # <-- importa aquí
from app.models.users import User


class UserService:
    @staticmethod
    async def get_all(db: AsyncSession):
        result = await db.execute(select(User))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).where(User.id_usuario == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_in):
        user_dict = user_in.dict()
        user_dict["contrasena"] = hash_password(user_dict["contrasena"])  # <---
        db_user = User(**user_dict)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def delete(db: AsyncSession, user_id: int):
        user = await UserService.get_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.commit()
        return user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str):
        from sqlalchemy.future import select

        from app.models.users import User

        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
