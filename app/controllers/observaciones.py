from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.schemas.observacion import ObservacionCreate, ObservacionRead
from app.services.observaciones import ObservacionesService

router = APIRouter()

@router.post("/", response_model=ObservacionRead, status_code=status.HTTP_201_CREATED)
async def create_observacion(observacion_in: ObservacionCreate, db: AsyncSession = Depends(get_db)):
    return await ObservacionesService.create(db, observacion_in)

@router.get("/cita/{id_cita}", response_model=list[ObservacionRead])
async def list_observaciones_by_cita(id_cita: int, db: AsyncSession = Depends(get_db)):
    return await ObservacionesService.get_by_cita(db, id_cita)

@router.delete("/{id_observacion}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observacion(id_observacion: int, db: AsyncSession = Depends(get_db)):
    deleted = await ObservacionesService.delete(db, id_observacion)
    if not deleted:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    return None
