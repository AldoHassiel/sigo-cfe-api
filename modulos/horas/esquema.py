from datetime import time
from typing import Annotated

from pydantic import StringConstraints
from sqlmodel import SQLModel

TextoObligatorio = Annotated[str, StringConstraints(min_length=1)]


class HorasExtrasBase(SQLModel):
    RPE: TextoObligatorio
    TOTAL: time


class HorasExtrasRespuesta(SQLModel):
    rpe: TextoObligatorio
    horas_totales: time
