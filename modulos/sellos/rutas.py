from fastapi import APIRouter, UploadFile

from dependencias import SessionDep
from modulos.sellos.esquemas import SelloDatos, SelloRespuesta
from nucleo.respuestas import RespuestaAPI
from nucleo.utils import leer_archivo, validar_datos

ruta = APIRouter(prefix="/sellos", tags=["Sellos"])


@ruta.get("/")
async def obtener_sellos():
    pass


@ruta.post("/importar", response_model=RespuestaAPI[list[dict]])
def importar_sellos(
    archivo: UploadFile, session: SessionDep
) -> RespuestaAPI[list[dict]]:
    datos_leidos = leer_archivo(archivo)
    datos_validados = validar_datos(datos_leidos, SelloDatos, "numsello")

    print(datos_validados)

    return RespuestaAPI(
        exito=True, mensaje="Datos importados con éxito", datos=list({})
    )
