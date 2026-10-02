from datetime import time, timedelta

from sqlmodel import Session, col, delete, insert, select

from nucleo.errores import ErrorImportacion

from .duracion import convertir_duracion, formatear_duracion
from .esquema import HorasExtrasBase, HorasExtrasRespuesta, RegistroHoras
from .modelo import HoraExtrasBD


def crear_respuesta_horas_extras(
    rpe: str,
    horas_totales: str | time | timedelta,
    limite_horas_semanales: float,
) -> HorasExtrasRespuesta:
    duracion = convertir_duracion(horas_totales)
    return HorasExtrasRespuesta(
        rpe=rpe,
        horas_totales=duracion,
        excede_limite_semanal=(
            duracion.total_seconds() > limite_horas_semanales * 3600
        ),
    )


def acumular_horas_extras(datos: list[RegistroHoras]):
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


def transformar_texto_a_esquema_horas(texto_crudo: str) -> list[RegistroHoras]:
    texto_lista = texto_crudo.split("\t")

    datos_transformados: list[RegistroHoras] = []

    INICIO = 17
    SALTO_A_HORA = 6
    SALTO_DE_HORA_A_RPE = 11

    indice = INICIO

    while indice < len(texto_lista) - 1:
        elemento_rpe = texto_lista[indice].split()
        if not elemento_rpe:
            raise ErrorImportacion("Falta el RPE de un registro del texto.")
        rpe = elemento_rpe[-1]

        indice += SALTO_A_HORA
        if indice >= len(texto_lista):
            raise ErrorImportacion(f"Falta el TOTAL del RPE {rpe}.")

        hora = texto_lista[indice]
        try:
            hora = formatear_duracion(convertir_duracion(hora))
        except ValueError as error:
            raise ErrorImportacion(
                f"TOTAL inválido para el RPE {rpe}: {hora!r}. {error}"
            ) from error
        indice += SALTO_DE_HORA_A_RPE

        datos_transformados.append({"RPE": rpe, "TOTAL": hora})

    if not datos_transformados:
        raise ErrorImportacion("El texto no contiene registros de horas extras.")

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
