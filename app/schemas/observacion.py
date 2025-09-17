from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ObservacionBase(BaseModel):
    id_cita: int
    id_psicologo: int
    texto: str

class ObservacionCreate(ObservacionBase):
    pass

class ObservacionRead(ObservacionBase):
    id_observacion: int
    fecha_creacion: datetime

    class Config:
        orm_mode = True
