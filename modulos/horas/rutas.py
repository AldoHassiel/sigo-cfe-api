from typing import Annotated

from fastapi import APIRouter, Form, UploadFile
from sqlalchemy import insert
from sqlmodel import delete

from dependencias import SessionDep
from modulos.horas.modelo import HoraExtrasBD
from modulos.horas.servicio import (
    acumular_horas_extras,
    consultar_horas_extras,
    remplazar_horas_extras,
    transformar_texto_a_esquema_horas,
)

from nucleo.respuestas import RespuestaAPI
from nucleo.utils import leer_archivo, validar_datos

from .esquema import HorasExtrasBase, HorasExtrasRespuesta

ruta = APIRouter(
    prefix="/horas-extras",
    tags=["Horas Extras"],
    responses={422: {"model": RespuestaAPI[None]}, 500: {"model": RespuestaAPI[None]}},
)

RespuestaHorasExtras = RespuestaAPI[list[HorasExtrasRespuesta]]


@ruta.get("/", response_model=RespuestaHorasExtras)
def obtener_horas_extras(session: SessionDep) -> RespuestaHorasExtras:
    filas = consultar_horas_extras(session)

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron obtenidas exitosamente",
            "datos": filas,
        }
    )


@ruta.post("/importar")
async def importar_horas_extras(archivo: UploadFile, session: SessionDep):
    datos = leer_archivo(archivo)
    registros = validar_datos(datos, HorasExtrasBase)
    conjunto = acumular_horas_extras(registros)

    #with session.begin():
        #remplazar_horas_extras(
            #session, [{"RPE": rpe, "TOTAL": total} for rpe, total in conjunto.items()]
        #)

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron importadas exitosamente",
            "datos": conjunto,
        }
    )


@ruta.post("/importar-texto")
async def importar_texto_crudo(texto: Annotated[str, Form(...)], session: SessionDep):
    texto_limpio = transformar_texto_a_esquema_horas(texto)
    conjunto = acumular_horas_extras(texto_limpio)
    with session.begin():
        remplazar_horas_extras(
            session, [{"RPE": rpe, "TOTAL": total} for rpe, total in conjunto.items()]
        )

    return RespuestaHorasExtras.model_validate(
        {
            "exito": True,
            "mensaje": "Las horas extras fueron importadas exitosamente",
            "datos": conjunto,
        }
    )
