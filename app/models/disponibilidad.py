from sqlalchemy import Column, ForeignKey, Integer, String, Time

from .base import Base


class DisponibilidadPsicologo(Base):
    __tablename__ = "DisponibilidadPsicologo"

    id_disponibilidad = Column(Integer, primary_key=True, index=True)
    id_psicologo = Column(Integer, ForeignKey("Usuarios.id_usuario"), nullable=False)
    dia_semana = Column(String(10), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
