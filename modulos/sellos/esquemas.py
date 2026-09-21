from datetime import UTC, date, datetime
from typing import Annotated, Literal

from openpyxl.utils.datetime import from_excel
from pydantic import StringConstraints, field_validator
from sqlmodel import SQLModel

TextoObligatorio = Annotated[str, StringConstraints(min_length=1)]


class SelloDatos(SQLModel):
    numsello: TextoObligatorio
    rpe: TextoObligatorio
    fechaultimomovimiento: date
    cvearea: TextoObligatorio

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


class SelloRespuesta(SelloDatos):
    nombre_area: str
    estado: Literal["vencido", "proximo", "vigente"]
    dias_restantes: int
