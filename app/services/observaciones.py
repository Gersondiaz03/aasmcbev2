from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.observacion import Observacion

class ObservacionesService:
    @staticmethod
    async def create(db: AsyncSession, observacion_in):
        db_observacion = Observacion(**observacion_in.dict())
        db.add(db_observacion)
        await db.commit()
        await db.refresh(db_observacion)
        return db_observacion

    @staticmethod
    async def get_by_cita(db: AsyncSession, id_cita: int):
        result = await db.execute(select(Observacion).where(Observacion.id_cita == id_cita))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, id_observacion: int):
        result = await db.execute(select(Observacion).where(Observacion.id_observacion == id_observacion))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, id_observacion: int):
        observacion = await ObservacionesService.get_by_id(db, id_observacion)
        if observacion:
            await db.delete(observacion)
            await db.commit()
            return True
        return False
