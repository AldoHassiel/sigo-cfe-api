from sqlmodel import Field, Relationship, SQLModel

from modulos.sellos import modelo


class Area(SQLModel, table=True):
    id: str = Field(primary_key=True)
    nombre: str

    sellos: list["Sello"] = Relationship(back_populates="area")
