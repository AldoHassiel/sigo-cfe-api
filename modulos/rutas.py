from fastapi import APIRouter

from .horas.rutas import ruta as horas_router
from .sellos.rutas import ruta as sellos_router

api_router = APIRouter()

api_router.include_router(sellos_router)
api_router.include_router(horas_router)
