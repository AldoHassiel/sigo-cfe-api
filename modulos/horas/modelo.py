from sqlmodel import Field
from .esquema import HorasExtrasBase


class HoraExtrasBD(HorasExtrasBase, table=True):
    rpe: str = Field(primary_key=True)
