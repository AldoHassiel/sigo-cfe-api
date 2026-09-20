# ruff: noqa: F401
from sqlmodel import Field, SQLModel

from .sellos.modelo import Sello


class Area(SQLModel, table=True):
    id: str = Field(primary_key=True)
    nombre: str
