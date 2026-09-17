from contextlib import asynccontextmanager

from fastapi import FastAPI

from modulos.sellos.rutas import ruta as rutas_sellos
from nucleo.db import crear_tablas


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(title="SIGO CFE API", version="0.0.1", lifespan=lifespan)

app.include_router(rutas_sellos)


@app.get("/")
async def root():
    return {"bienvenido": "a SIGO CFE API"}
