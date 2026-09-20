from fastapi import APIRouter

from .sellos.rutas import ruta as sellos_router

api_router = APIRouter()

api_router.include_router(sellos_router)
