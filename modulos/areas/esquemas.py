from sqlmodel import SQLModel


class AreaRespuesta(SQLModel):
    id: str
    nombre: str