from typing import Annotated, Literal
from sqlmodel import SQLModel 
from datetime import UTC, date, datetime
from openpyxl.utils.datetime import from_excel

from pydantic import StringConstraints, field_validator

TextoObligatorio = Annotated[str, StringConstraints(min_length=1)]

class MedidorDatos (SQLModel):
    nummedidor: TextoObligatorio
    cvearea: TextoObligatorio
    rpe: TextoObligatorio
    fechaultimomovimiento: date

    @field_validator("fechaultimomovimiento", mode="before")
    @classmethod
    def convertir_fecha(cls, valor):
        if isinstance(valor, (str, int, float)):
            texto = str(valor).strip()
            if len(texto) == 8 and texto.isdigit():
                return datetime.strptime(texto, "%d%m%Y").replace(tzinfo=UTC).date()
            if "/" in texto:
                return datetime.strptime(texto, "%d/%m/%Y").replace(tzinfo=UTC).date()
            if texto.replace(".", "", 1).isdigit():
                return from_excel(float(texto)).date()
        return valor

class MedidorRespuesta(MedidorDatos):
    nombre_area: str
    estado: Literal["vencido", "proximo", "vigente"]
    dias_restantes: int
