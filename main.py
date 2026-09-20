from contextlib import asynccontextmanager

from fastapi import FastAPI

from modulos.rutas import api_router
from nucleo.db import crear_tablas
from nucleo.errores import registrar_manejadores


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(title="SIGO CFE API", version="0.0.1", lifespan=lifespan)

registrar_manejadores(app)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"bienvenido": "a SIGO CFE API"}
