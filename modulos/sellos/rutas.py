from typing import Annotated

from fastapi import APIRouter, Query, UploadFile

from dependencias import SessionDep
from modulos.sellos.esquemas import SelloDatos, SelloRespuesta
from modulos.sellos.servicio import consultar_sellos, remplazar_sellos
from nucleo.respuestas import RespuestaAPI
from nucleo.utils import leer_archivo, validar_datos

ruta = APIRouter(
    prefix="/sellos",
    tags=["Sellos"],
    responses={
        422: {"model": RespuestaAPI[None]},
        500: {"model": RespuestaAPI[None]},
    },
)

RespuestaSellos = RespuestaAPI[list[SelloRespuesta]]
DiasAviso = Annotated[int, Query(ge=0, le=30)]


@ruta.get("/", response_model=RespuestaSellos)
async def obtener_sellos(
    session: SessionDep, dias_aviso: DiasAviso = 7
) -> RespuestaSellos:
    filas = consultar_sellos(session, dias_aviso)

    respuesta = RespuestaSellos.model_validate(
        {"exito": True, "mensaje": "Sellos obtenidos correctamente", "datos": filas}
    )

    return respuesta


@ruta.post("/importar", response_model=RespuestaSellos)
def importar_sellos(
    archivo: UploadFile, session: SessionDep, dias_aviso: DiasAviso = 7
) -> RespuestaSellos:
    datos = leer_archivo(archivo)
    registros = validar_datos(datos, SelloDatos, "numsello")

    with session.begin():
        remplazar_sellos(session, registros)

        filas = consultar_sellos(session, dias_aviso)

        respuesta = RespuestaSellos.model_validate(
            {
                "exito": True,
                "mensaje": f"Se importaron {len(registros)} sellos.",
                "datos": filas,
            }
        )


    return respuesta
