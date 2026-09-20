from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class RespuestaAPI(BaseModel, Generic[T]):
    exito: bool
    mensaje: str
    datos: T | None = None
