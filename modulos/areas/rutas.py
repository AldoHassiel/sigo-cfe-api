from fastapi import APIRouter

from dependencias import SessionDep
from modulos.areas.esquemas import AreaRespuesta
from modulos.areas.servicio import consultar_areas
from nucleo.respuestas import RespuestaAPI

ruta = APIRouter(
    prefix="/areas",
    tags=["Áreas"],
    responses={500: {"model": RespuestaAPI[None]}},
)

RespuestaAreas = RespuestaAPI[list[AreaRespuesta]]


@ruta.get("/", response_model=RespuestaAreas)
def obtener_areas(session: SessionDep) -> RespuestaAreas:
    areas = consultar_areas(session)

    return RespuestaAreas.model_validate(
        {
            "exito": True,
            "mensaje": "Las áreas fueron obtenidas exitosamente",
            "datos": areas,
        }
    )