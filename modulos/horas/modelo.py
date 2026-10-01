from sqlmodel import Field

from .esquema import HorasExtrasBase


class HoraExtrasBD(HorasExtrasBase, table=True):
    RPE: str = Field(primary_key=True)
