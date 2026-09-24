from fastapi import APIRouter, UploadFile

from dependencias import SessionDep
from modulos.horas.servicio import acumular_horas_extras
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
