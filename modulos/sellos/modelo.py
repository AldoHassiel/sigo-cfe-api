from sqlmodel import Field

from modulos.sellos.esquemas import SelloDatos


class Sello(SelloDatos, table=True):
    numsello: str = Field(primary_key=True)
    cvearea: str = Field(foreign_key="area.id")
