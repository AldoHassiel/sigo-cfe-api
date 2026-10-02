from datetime import time, timedelta
from typing import Annotated, TypedDict

from pydantic import BeforeValidator, PlainSerializer, StringConstraints, WithJsonSchema
from sqlmodel import SQLModel

from .duracion import convertir_duracion, formatear_duracion

TextoObligatorio = Annotated[str, StringConstraints(min_length=1)]
DuracionHoras = Annotated[
    timedelta,
    BeforeValidator(convertir_duracion),
    PlainSerializer(formatear_duracion, return_type=str, when_used="json"),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^[0-9]+:[0-5]?[0-9](?::[0-5]?[0-9](?:\.[0-9]{1,6})?)?$",
            "examples": ["3:0", "5:7", "24:00:00", "125:30:00"],
        }
    ),
]


class HorasExtrasBase(SQLModel):
    RPE: TextoObligatorio
    TOTAL: DuracionHoras


class HorasExtrasRespuesta(SQLModel):
    rpe: TextoObligatorio
    horas_totales: DuracionHoras
    excede_limite_semanal: bool


class RegistroHoras(TypedDict):
    RPE: str
    TOTAL: str | time | timedelta
