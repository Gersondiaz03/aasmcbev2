from sqlalchemy import Column, Integer, String

from .base import Base


class Role(Base):
    __tablename__ = "Roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
