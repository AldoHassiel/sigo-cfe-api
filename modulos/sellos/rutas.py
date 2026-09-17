from fastapi import APIRouter, UploadFile

from dependencias import SessionDep
from modulos.sellos.modelo import Sello
from nucleo.utils import dataframe_a_sellos, leer_archivo

ruta = APIRouter(prefix="/sellos", tags=["Sellos"])


@ruta.get("/")
async def obtener_sellos():
    pass


@ruta.post("/importar")
async def importar_sellos(archivo: UploadFile, session: SessionDep):
    datos = leer_archivo(archivo)
    datos_filtrados = dataframe_a_sellos(datos)
    sellos = [Sello.model_validate(dato) for dato in datos_filtrados]

    try:
        session.add_all(sellos)
        session.commit()
    except Exception:
        session.rollback()
        raise

    return len(sellos)
