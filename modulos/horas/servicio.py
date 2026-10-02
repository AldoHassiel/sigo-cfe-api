from datetime import time, timedelta

from sqlmodel import Session, col, select, insert, delete

from .duracion import convertir_duracion, formatear_duracion
from .esquema import HorasExtrasBase
from .modelo import HoraExtrasBD


def acumular_horas_extras(datos: list[dict[str, str | time | timedelta]]):
    conjunto_rpe = set()
    diccionario_de_horas: dict[str, timedelta] = {}

    for empleado in datos:
        rpe = empleado["RPE"]
        hora = empleado["TOTAL"]

        horas_extras = convertir_duracion(hora)
        if rpe in conjunto_rpe:
            diccionario_de_horas[rpe] += horas_extras
            continue

        diccionario_de_horas[rpe] = horas_extras
        conjunto_rpe.add(rpe)

    resultado = {}
    for rpe, duracion in diccionario_de_horas.items():
        resultado[rpe] = formatear_duracion(duracion)

    return resultado


def transformar_texto_a_esquema_horas(texto_crudo: str):
    texto_lista = texto_crudo.split("\t")

    datos_transformados: list[dict[str, str]] = []

    INICIO = 17
    SALTO_A_HORA = 6
    SALTO_DE_HORA_A_RPE = 11

    indice = INICIO

    while indice < len(texto_lista) - 1:
        elemento_rpe = texto_lista[indice]
        indice_rpe = 2 if "SIN AUTORIZACION" in elemento_rpe else 1
        rpe = elemento_rpe.split(" ")[indice_rpe]

        indice += SALTO_A_HORA

        hora = texto_lista[indice]
        indice += SALTO_DE_HORA_A_RPE

        datos_transformados.append({"RPE": rpe, "TOTAL": hora})

    return datos_transformados


def consultar_horas_extras(session: Session):
    consulta = select(
        col(HoraExtrasBD.RPE).label("rpe"),
        col(HoraExtrasBD.TOTAL).label("horas_totales"),
    ).order_by(col(HoraExtrasBD.RPE))

    return session.execute(consulta).mappings().all()


def remplazar_horas_extras(session: Session, datos: list[dict]) -> None:
    registros = [HorasExtrasBase.model_validate(dato).model_dump() for dato in datos]
    session.exec(delete(HoraExtrasBD))
    if registros:
        session.exec(insert(HoraExtrasBD), params=registros)
