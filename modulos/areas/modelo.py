from sqlmodel import Field, SQLModel


class Area(SQLModel, table=True):
    id: str = Field(primary_key=True)
    nombre: str