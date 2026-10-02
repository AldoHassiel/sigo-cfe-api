import re
from datetime import time, timedelta


def convertir_duracion(valor: str | time | timedelta) -> timedelta:
    if isinstance(valor, timedelta):
        duracion = valor
    elif isinstance(valor, time):
        duracion = timedelta(
            hours=valor.hour,
            minutes=valor.minute,
            seconds=valor.second,
            microseconds=valor.microsecond,
        )
    elif isinstance(valor, str):
        partes = re.fullmatch(
            r"([0-9]+):([0-5]?[0-9])(?::([0-5]?[0-9])(?:\.([0-9]{1,6}))?)?",
            valor.strip(),
        )
        if partes is None:
            raise ValueError("Usa una duración HH:MM o HH:MM:SS.")
        horas, minutos, segundos, fraccion = partes.groups()
        try:
            duracion = timedelta(
                hours=int(horas),
                minutes=int(minutos),
                seconds=int(segundos or 0),
                microseconds=int((fraccion or "").ljust(6, "0")),
            )
        except OverflowError as error:
            raise ValueError("La duración es demasiado grande.") from error
    else:
        raise ValueError("Usa una duración HH:MM o HH:MM:SS.")

    if duracion < timedelta():
        raise ValueError("La duración no puede ser negativa.")
    return duracion


def formatear_duracion(duracion: timedelta) -> str:
    horas, resto = divmod(duracion.days * 86400 + duracion.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    resultado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    if duracion.microseconds:
        resultado += f".{duracion.microseconds:06d}".rstrip("0")
    return resultado
