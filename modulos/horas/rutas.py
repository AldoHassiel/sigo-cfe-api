from fastapi import APIRouter

from nucleo.respuestas import RespuestaAPI

from .esquema import HorasExtrasRespuesta

ruta = APIRouter(
    prefix="/horas-extras",
    tags=["Horas Extras"],
    responses={422: {"model": RespuestaAPI[None]}, 500: {"model": RespuestaAPI[None]}},
)

RespuestaHorasExtras = RespuestaAPI[HorasExtrasRespuesta]


@ruta.post("/importar", response_model=RespuestaHorasExtras)
async def importar_horas_extras():
    pass
