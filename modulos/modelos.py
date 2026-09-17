from sqlmodel import SQLModel, Field, Relationship

class Area (SQLModel, table = True):
    id : str = Field(primary_key = True)
    nombre : str

    sellos: list["Sello"] = Relationship(back_populates="area")

