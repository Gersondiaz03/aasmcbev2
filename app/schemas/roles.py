from pydantic import BaseModel


class RoleBase(BaseModel):
    nombre_rol: str


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id_rol: int

    class Config:
        orm_mode = True
