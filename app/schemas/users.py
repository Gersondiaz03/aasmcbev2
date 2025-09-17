# backend/app/schemas/users.py
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    contrasena: str
    id_rol: int


class UserRead(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    id_rol: int

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    email: EmailStr | None = None
    contrasena: str | None = None
    id_rol: int | None = None
