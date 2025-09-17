from sqlalchemy import Column, Integer, String

from .base import Base


class User(Base):
    __tablename__ = "Usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    contrasena = Column(String, nullable=False)
    id_rol = Column(Integer)  # FK a Roles
