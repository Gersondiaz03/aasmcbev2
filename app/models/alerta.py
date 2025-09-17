from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, text

from .base import Base


class Alerta(Base):
    __tablename__ = "Alertas"
    id_alerta = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    texto = Column(String, nullable=False)
    severidad = Column(String(20), nullable=False, default="ALTA")
    fecha_creacion = Column(DateTime(timezone=True), server_default=text("now()"))
