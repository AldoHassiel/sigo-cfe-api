from typing import Annotated

from fastapi import APIRouter, Form, Query, UploadFile

from dependencias import SessionDep
from modulos.horas.servicio import (
    acumular_horas_extras,
    consultar_horas_extras,
    crear_respuesta_horas_extras,
    remplazar_horas_extras,
    transformar_texto_a_esquema_horas,
)
from nucleo.respuestas import RespuestaAPI
from nucleo.utils import leer_archivo, validar_datos

from .esquema import HorasExtrasBase, HorasExtrasRespuesta, RegistroHoras

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
            "Límite de horas extras por RPE para la semana importada. "
            "El indicador es verdadero solo cuando el total supera este valor."
        ),
    ),
]


@ruta.get("/", response_model=RespuestaHorasExtras)
def obtener_horas_extras(
    session: SessionDep,
    limite_horas_semanales: LimiteHorasSemanales = LIMITE_HORAS_SEMANALES_PREDETERMINADO,
) -> RespuestaHorasExtras:
    filas = consultar_horas_extras(session)

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron obtenidas exitosamente",
            "datos": [
                crear_respuesta_horas_extras(
                    fila["rpe"], fila["horas_totales"], limite_horas_semanales
                )
                for fila in filas
            ],
        }
    )


@ruta.post("/importar", response_model=RespuestaHorasExtras)
async def importar_horas_extras(
    archivo: UploadFile,
    session: SessionDep,
    limite_horas_semanales: LimiteHorasSemanales = LIMITE_HORAS_SEMANALES_PREDETERMINADO,
) -> RespuestaHorasExtras:
    datos = leer_archivo(archivo)
    registros = validar_datos(datos, HorasExtrasBase)
    registros_tipados: list[RegistroHoras] = [
        {"RPE": registro["RPE"], "TOTAL": registro["TOTAL"]} for registro in registros
    ]
    conjunto = acumular_horas_extras(registros_tipados)
    lista_horas = [
        crear_respuesta_horas_extras(rpe, hora, limite_horas_semanales)
        for rpe, hora in conjunto.items()
    ]

    with session.begin():
        remplazar_horas_extras(
            session, [{"RPE": rpe, "TOTAL": total} for rpe, total in conjunto.items()]
        )

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron importadas exitosamente",
            "datos": lista_horas,
        }
    )


@ruta.post("/importar-texto", response_model=RespuestaHorasExtras)
async def importar_texto_crudo(
    texto: Annotated[str, Form(...)],
    session: SessionDep,
    limite_horas_semanales: LimiteHorasSemanales = LIMITE_HORAS_SEMANALES_PREDETERMINADO,
) -> RespuestaHorasExtras:
    texto_limpio = transformar_texto_a_esquema_horas(texto)
    conjunto = acumular_horas_extras(texto_limpio)
    lista_horas = [
        crear_respuesta_horas_extras(rpe, total, limite_horas_semanales)
        for rpe, total in conjunto.items()
    ]

    with session.begin():
        remplazar_horas_extras(
            session, [{"RPE": rpe, "TOTAL": total} for rpe, total in conjunto.items()]
        )

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron importadas exitosamente",
            "datos": lista_horas,
        }
    )
