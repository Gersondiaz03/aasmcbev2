from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from .base import Base

class Observacion(Base):
    __tablename__ = "Observaciones"
    id_observacion = Column(Integer, primary_key=True, index=True)
    id_cita = Column(Integer, ForeignKey("Citas.id_cita"), nullable=False)
    id_psicologo = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    texto = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
