from typing import Annotated

from fastapi import APIRouter, Form, UploadFile

from dependencias import SessionDep
from modulos.horas.servicio import (
    acumular_horas_extras,
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

RespuestaHorasExtras = RespuestaAPI[HorasExtrasRespuesta]


@ruta.post("/importar")
async def importar_horas_extras(archivo: UploadFile, session: SessionDep):
    datos = leer_archivo(archivo)
    registros = validar_datos(datos, HorasExtrasBase)
    conjunto = acumular_horas_extras(registros)

    return conjunto


@ruta.post("/importar-texto")
async def importar_texto_crudo(texto: Annotated[str, Form(...)]):
    texto_limpio = transformar_texto_a_esquema_horas(texto)

    return texto_limpio
