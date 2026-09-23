from typing import Annotated

from fastapi import APIRouter, Query, UploadFile

from dependencias import SessionDep
from modulos.medidores.esquemas import MedidorDatos, MedidorRespuesta
from modulos.medidores.servicio import consultar_medidores, remplazar_medidores
from nucleo.respuestas import RespuestaAPI
from nucleo.utils import leer_archivo, validar_datos

ruta = APIRouter(
    prefix="/medidores",
    tags=["Medidores"],
    responses={
        422: {"model": RespuestaAPI[None]},
        500: {"model": RespuestaAPI[None]},
    },
)

RespuestaMedidores = RespuestaAPI[list[MedidorRespuesta]]
DiasAviso = Annotated[int, Query(ge=0, le=30)]


@ruta.get("/", response_model=RespuestaMedidores)
async def obtener_medidores(
    session: SessionDep, dias_aviso: DiasAviso = 7
) -> RespuestaMedidores:
    filas = consultar_medidores(session, dias_aviso)

    respuesta = RespuestaMedidores.model_validate(
        {
            "exito": True,
            "mensaje": "Los medidores fueron obtenidos exitosamente",
            "datos": filas,
        }
    )
    return respuesta


@ruta.post("/importar", response_model=RespuestaMedidores)
def importar_medidores(
    archivo: UploadFile, session: SessionDep, dias_aviso: DiasAviso = 7
) -> RespuestaMedidores:
    datos = leer_archivo(archivo)
    registros = validar_datos(datos, MedidorDatos, "nummedidor")

    with session.begin():
        remplazar_medidores(session, registros)

        filas = consultar_medidores(session, dias_aviso)

        respuesta = RespuestaMedidores.model_validate(
            {
                "exito": True,
                "mensaje": "Los medidores fueron importados exitosamente",
                "datos": filas,
            }
        )

    return respuesta
