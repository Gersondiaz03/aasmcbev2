from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertaBase(BaseModel):
    id_estudiante: int
    texto: str
    severidad: str = "ALTA"


class AlertaCreate(AlertaBase):
    pass


class AlertaRead(AlertaBase):
    id_alerta: int
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)
