from datetime import datetime
from pydantic import BaseModel


class CitaBase(BaseModel):
    id_estudiante: int
    id_psicologo: int
    fecha_hora_inicio: str
    fecha_hora_fin: str
    modalidad: str


class CitaCreate(BaseModel):
    id_estudiante: int
    id_psicologo: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    modalidad: str


class CitaRead(BaseModel):
    id_cita: int
    id_estudiante: int
    id_psicologo: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
    modalidad: str

    class Config:
        orm_mode = True


class CitaReschedule(BaseModel):
    fecha_hora_inicio: datetime
    fecha_hora_fin: datetime
