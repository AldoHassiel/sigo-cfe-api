from sqlmodel import Field

from modulos.medidores.esquemas import MedidorDatos


class Medidor(MedidorDatos, table=True):
    nummedidor: str = Field(primary_key=True)
    cvearea: str = Field(foreign_key="area.id")
