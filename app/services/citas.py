from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.citas import Cita
from app.models.users import User


class CitasService:
    @staticmethod
    async def get_all(db: AsyncSession):
        # Fetch citas with psicologo and estudiante names in a single query
        from sqlalchemy.orm import aliased

        P = aliased(User)
        E = aliased(User)
        stmt = (
            select(
                Cita,
                P.nombre.label("p_nombre"),
                P.apellido.label("p_apellido"),
                E.nombre.label("e_nombre"),
                E.apellido.label("e_apellido"),
            )
            .join(P, Cita.id_psicologo == P.id_usuario)
            .join(E, Cita.id_estudiante == E.id_usuario)
        )
        result = await db.execute(stmt)
        rows = result.all()
        citas = []
        for cita, p_nombre, p_apellido, e_nombre, e_apellido in rows:
            citas.append(
                {
                    "id_cita": cita.id_cita,
                    "id_estudiante": cita.id_estudiante,
                    "id_psicologo": cita.id_psicologo,
                    "fecha_hora_inicio": cita.fecha_hora_inicio,
                    "fecha_hora_fin": cita.fecha_hora_fin,
                    "modalidad": cita.modalidad,
                    "psicologo": f"{p_nombre} {p_apellido}",
                    "estudiante": f"{e_nombre} {e_apellido}",
                }
            )
        return citas

    @staticmethod
    async def get_by_id(db: AsyncSession, cita_id: int):
        result = await db.execute(select(Cita).where(Cita.id_cita == cita_id))
        cita = result.scalar_one_or_none()
        if cita:
            return await CitasService.enriched_cita(db, cita)
        return None

    @staticmethod
    async def create(db: AsyncSession, cita_in):
        db_cita = Cita(**cita_in.dict())
        db.add(db_cita)
        await db.commit()
        await db.refresh(db_cita)
        return await CitasService.enriched_cita(db, db_cita)

    @staticmethod
    async def delete(db: AsyncSession, cita_id: int):
        cita = await CitasService.get_by_id(db, cita_id)
        if cita:
            # get_by_id returns enriched dict, need to fetch the actual model instance
            result = await db.execute(select(Cita).where(Cita.id_cita == cita_id))
            cita_obj = result.scalar_one_or_none()
            if cita_obj:
                await db.delete(cita_obj)
                await db.commit()
        return cita

    @staticmethod
    async def get_by_estudiante(db: AsyncSession, id_estudiante: int):
        result = await db.execute(
            select(Cita).where(Cita.id_estudiante == id_estudiante)
        )
        citas = result.scalars().all()
        return [await CitasService.enriched_cita(db, t) for t in citas]

    @staticmethod
    async def get_by_psicologo(db: AsyncSession, id_psicologo: int):
        result = await db.execute(select(Cita).where(Cita.id_psicologo == id_psicologo))
        citas = result.scalars().all()
        return [await CitasService.enriched_cita(db, t) for t in citas]

    @staticmethod
    async def enriched_cita(db: AsyncSession, cita: Cita):
        # Busca nombres de psicologo y estudiante, y nombre de la cita
        result = await db.execute(
            select(User).where(User.id_usuario == cita.id_psicologo)
        )
        psicologo = result.scalar_one_or_none()
        result = await db.execute(
            select(User).where(User.id_usuario == cita.id_estudiante)
        )
        estudiante = result.scalar_one_or_none()
        # No need to re-query cita, already have it
        return {
            "id_cita": cita.id_cita,
            "id_estudiante": cita.id_estudiante,
            "id_psicologo": cita.id_psicologo,
            "fecha_hora_inicio": cita.fecha_hora_inicio,
            "fecha_hora_fin": cita.fecha_hora_fin,
            "modalidad": cita.modalidad,
            "titulo": getattr(cita, "nombre_cita", None),
            "psicologo": (
                f"{psicologo.nombre} {psicologo.apellido}" if psicologo else None
            ),
            "estudiante": (
                f"{estudiante.nombre} {estudiante.apellido}" if estudiante else None
            ),
        }

    @staticmethod
    async def get_by_user_and_range(
        db: AsyncSession, usuario_id: int, from_date: str, to_date: str
    ):
        # from_date y to_date son strings tipo 'YYYY-MM-DD'
        from_dt = datetime.fromisoformat(from_date)
        to_dt = datetime.fromisoformat(to_date)

        stmt = select(Cita).where(
            and_(
                or_(
                    Cita.id_estudiante == usuario_id,
                    Cita.id_psicologo == usuario_id,
                ),
                Cita.fecha_hora_inicio >= from_dt,
                Cita.fecha_hora_fin <= to_dt,
            )
        )
        result = await db.execute(stmt)
        citas = result.scalars().all()
        return [await CitasService.enriched_cita(db, t) for t in citas]

    @staticmethod
    async def reschedule(db: AsyncSession, cita_id: int, reschedule_in):
        result = await db.execute(select(Cita).where(Cita.id_cita == cita_id))
        cita = result.scalar_one_or_none()
        if not cita:
            return None
        now = datetime.now(timezone.utc)
        cita_fecha_inicio = cita.fecha_hora_inicio
        if cita_fecha_inicio.tzinfo is None:
            cita_fecha_inicio = cita_fecha_inicio.replace(tzinfo=timezone.utc)
        # Only allow reschedule if cita is more than 24h away
        if (cita_fecha_inicio - now).total_seconds() < 24 * 3600:
            # Not allowed to reschedule if cita is less than 24h away
            return None
        cita.fecha_hora_inicio = reschedule_in.fecha_hora_inicio
        cita.fecha_hora_fin = reschedule_in.fecha_hora_fin
        await db.commit()
        await db.refresh(cita)
        return await CitasService.enriched_cita(db, cita)
