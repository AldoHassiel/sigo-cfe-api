from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modulos.rutas import api_router
from nucleo.db import crear_tablas
from nucleo.errores import registrar_manejadores

origins = [
    "http://localhost:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(title="SIGO CFE API", version="0.0.1", lifespan=lifespan)

registrar_manejadores(app)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"bienvenido": "a SIGO CFE API"}
