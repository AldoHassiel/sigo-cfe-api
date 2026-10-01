from datetime import time, timedelta


def acumular_horas_extras(datos: list[dict[str, str | time]]):
    conjunto_rpe = set()
    diccionario_de_horas: dict[str, timedelta] = {}

    for empleado in datos:
        rpe = empleado["RPE"]
        hora = empleado["TOTAL"]

        # timedelta admite duraciones mayores a 24 horas.
        if isinstance(hora, str):
            partes = hora.strip().split(":")
            if len(partes) == 2:
                partes.append("0")
            elif len(partes) != 3:
                raise ValueError(f"Formato de duración inválido: {hora!r}")

            horas, minutos, segundos = map(int, partes)
            if horas < 0 or not (0 <= minutos < 60 and 0 <= segundos < 60):
                raise ValueError(f"Duración inválida: {hora!r}")

            horas_extras = timedelta(hours=horas, minutes=minutos, seconds=segundos)
        else:
            horas_extras = timedelta(
                hours=hora.hour,
                minutes=hora.minute,
                seconds=hora.second,
                microseconds=hora.microsecond,
            )
        if rpe in conjunto_rpe:
            diccionario_de_horas[rpe] += horas_extras
            continue

        diccionario_de_horas[rpe] = horas_extras
        conjunto_rpe.add(rpe)

    resultado = {}
    for rpe, duracion in diccionario_de_horas.items():
        horas, resto = divmod(int(duracion.total_seconds()), 3600)
        minutos, segundos = divmod(resto, 60)
        resultado[rpe] = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

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
