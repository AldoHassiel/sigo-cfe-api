from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile

from dependencias import SessionDep
from modulos.horas.importacion import importar_registros
from modulos.horas.servicio import (
    consultar_horas_extras,
    remplazar_registros_horas_extras,
)
from nucleo.respuestas import RespuestaAPI

from .esquema import HorasExtrasRespuesta

ruta = APIRouter(
    prefix="/horas-extras",
    tags=["Horas Extras"],
    responses={422: {"model": RespuestaAPI[None]}, 500: {"model": RespuestaAPI[None]}},
)

RespuestaHorasExtras = RespuestaAPI[list[HorasExtrasRespuesta]]
LIMITE_HORAS_SEMANALES_PREDETERMINADO = 9.0
LimiteHorasSemanales = Annotated[
    float,
    Query(
        ge=0,
        allow_inf_nan=False,
        description=(
            "Límite de horas extras por RPE en cada semana. "
            "El indicador es verdadero cuando al menos una semana supera este valor."
        ),
    ),
]


@ruta.get("/", response_model=RespuestaHorasExtras)
def obtener_horas_extras(
    session: SessionDep,
    limite_horas_semanales: LimiteHorasSemanales = LIMITE_HORAS_SEMANALES_PREDETERMINADO,
) -> RespuestaHorasExtras:
    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron obtenidas exitosamente",
            "datos": consultar_horas_extras(session, limite_horas_semanales),
        }
    )


@ruta.post("/importar", response_model=RespuestaHorasExtras)
def importar_horas_extras(
    session: SessionDep,
    archivos: Annotated[
        list[UploadFile] | None,
        File(description="Uno o varios archivos .xlsx, .xls o .csv."),
    ] = None,
    textos: Annotated[
        list[str] | None,
        Form(description="Una o varias tablas copiadas del sistema o de Excel."),
    ] = None,
    limite_horas_semanales: LimiteHorasSemanales = LIMITE_HORAS_SEMANALES_PREDETERMINADO,
) -> RespuestaHorasExtras:
    registros = importar_registros(archivos or [], textos or [])

    with session.begin():
        remplazar_registros_horas_extras(session, registros)

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron importadas exitosamente",
            "datos": consultar_horas_extras(session, limite_horas_semanales),
        }
    )
