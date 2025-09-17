from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.sql import func

from .base import Base


class Cita(Base):
    __tablename__ = "Citas"
    id_cita = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    id_psicologo = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    fecha_hora_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_hora_fin = Column(DateTime(timezone=True), nullable=False)
    modalidad = Column(String(20), nullable=False)  # 'presencial', 'videollamada'
    fecha_solicitud = Column(DateTime(timezone=True), server_default=text("now()"))
    fecha_confirmacion = Column(DateTime(timezone=True), nullable=True)
    fecha_cancelacion = Column(DateTime(timezone=True), nullable=True)
