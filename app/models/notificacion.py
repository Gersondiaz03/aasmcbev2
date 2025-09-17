from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from .base import Base

class Notificacion(Base):
    __tablename__ = "Notificaciones"
    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=True)
    id_psicologo = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=True)
    titulo = Column(String(255), nullable=False)
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
