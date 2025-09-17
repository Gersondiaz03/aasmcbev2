from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class NotificacionBase(BaseModel):
    id_estudiante: Optional[int] = None
    id_psicologo: Optional[int] = None
    titulo: str


class NotificacionCreate(NotificacionBase):
    pass


class NotificacionRead(NotificacionBase):
    id_notificacion: int
    leida: bool
    fecha_creacion: datetime

    # Pydantic v2: enable ORM attributes support for from_orm
    model_config = ConfigDict(from_attributes=True)
