from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg2 import Error as PsycopError
from sqlalchemy.exc import DataError, IntegrityError
from starlette.exceptions import HTTPException

from nucleo.respuestas import RespuestaAPI


class ErrorImportacion(ValueError):
    pass


def respuesta_error(codigo: int, mensaje: str, headers=None) -> JSONResponse:
    contenido = RespuestaAPI[None](exito=False, mensaje=mensaje, datos=None)

    return JSONResponse(
        status_code=codigo, content=contenido.model_dump(mode="json"), headers=headers
    )


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorImportacion)
    async def error_importacion(_request: Request, error):
        return respuesta_error(422, str(error))

    @app.exception_handler(RequestValidationError)
    async def error_peticion(_request: Request, error):
        return respuesta_error(
            422, "La petición contiene datos faltantes o parámetros inválidos."
        )

    @app.exception_handler(IntegrityError)
    async def error_integridad(_request: Request, error: IntegrityError):
        codigo = error.orig.pgcode if isinstance(error.orig, PsycopError) else None

        mensajes: dict[str, str] = {
            "23503": "Hay una referencia que no existe, como un área inválida.",
            "23505": "Hay valores duplicados en un campo que debe ser único.",
            "23502": "Falta un valor obligatorio.",
            "23514": "Un registro incumple una restricción de la tabla.",
        }

        mensaje = mensajes.get(codigo) if codigo is not None else None

        return respuesta_error(
            422,
            mensaje or "Los datos incumplen una restricción de la base de datos.",
        )

    @app.exception_handler(DataError)
    async def error_datos(_request: Request, error):
        return respuesta_error(
            422, "Hay un valor incompatible con el tipo o tamaño de una columna"
        )

    @app.exception_handler(HTTPException)
    async def error_http(_request: Request, error):
        return respuesta_error(
            error.status_code, "No se pudo procesar la petición", headers=error.headers
        )

    @app.exception_handler(Exception)
    async def error_inesperado(_request: Request, error):
        return respuesta_error(
            500, "Ocurrió un error interno al procesar la operación."
        )
