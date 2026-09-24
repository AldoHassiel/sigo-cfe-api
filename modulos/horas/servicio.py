from datetime import time


def acumular_horas_extras(datos: list[dict[str, time]]):
    conjunto_rpe = set()
    diccionario_de_horas = dict[str, time]

    for empleado in datos:
        rpe = empleado["RPE"]
        if rpe in conjunto_rpe:
            diccionario_de_horas[rpe] = diccionario_de_horas[rpe] + empleado["TOTAL"]
            continue

        diccionario_de_horas[rpe] = empleado["TOTAL"]

    return conjunto_rpe
