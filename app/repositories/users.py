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
