from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.citas import CitaCreate, CitaRead, CitaReschedule
from app.services.citas import CitasService

router = APIRouter()


@router.post("/", response_model=CitaRead, status_code=status.HTTP_201_CREATED)
async def create_cita(cita_in: CitaCreate, db: AsyncSession = Depends(get_db)):
    # Forzamos que los campos sean obligatorios (Pydantic ya lo hace, pero doble check)
    if not cita_in.id_estudiante or not cita_in.id_psicologo:
        raise HTTPException(
            status_code=400, detail="Estudiante y Psicólogo son obligatorios"
        )
    return await CitasService.create(db, cita_in)


@router.get("/estudiante/{id_estudiante}", response_model=list[CitaRead])
async def list_citas_estudiante(id_estudiante: int, db: AsyncSession = Depends(get_db)):
    return await CitasService.get_by_estudiante(db, id_estudiante)


@router.get("/psicologo/{id_psicologo}", response_model=list[CitaRead])
async def list_citas_psicologo(id_psicologo: int, db: AsyncSession = Depends(get_db)):
    return await CitasService.get_by_psicologo(db, id_psicologo)


@router.get("/calendar", response_model=list[CitaRead])
async def calendar(
    usuario_id: int,
    from_date: str,
    to_date: str,
    db: AsyncSession = Depends(get_db),
):
    return await CitasService.get_by_user_and_range(db, usuario_id, from_date, to_date)


@router.delete("/{id_cita}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cita(id_cita: int, db: AsyncSession = Depends(get_db)):
    deleted = await CitasService.delete(db, id_cita)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return None


@router.patch("/reschedule/{id_cita}", response_model=CitaRead)
async def reschedule_cita(
    id_cita: int,
    reschedule_in: CitaReschedule,
    db: AsyncSession = Depends(get_db),
):
    cita = await CitasService.reschedule(db, id_cita, reschedule_in)
    if not cita:
        raise HTTPException(
            status_code=404, detail="Cita no encontrada o no se puede reprogramar"
        )
    return cita


@router.get("/{id_cita}", response_model=CitaRead)
async def get_cita(id_cita: int, db: AsyncSession = Depends(get_db)):
    cita = await CitasService.get_by_id(db, id_cita)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita


@router.get("/", response_model=list[CitaRead])
async def list_citas(db: AsyncSession = Depends(get_db)):
    return await CitasService.get_all(db)
