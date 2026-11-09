import csv
import io
import math
import re
import unicodedata
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from nucleo.errores import ErrorImportacion

from .duracion import convertir_duracion, formatear_duracion
from .modelo import RegistroHoraExtra

EXTENSIONES_PERMITIDAS = {".csv", ".xlsx", ".xls"}
MAXIMO_ERRORES_REPORTADOS = 15
UN_DIA = timedelta(days=1)

COLUMNAS_OBLIGATORIAS = {
    "RPE": "rpe",
    "LABORADO": "laborado",
    "INICIO": "inicio",
    "TERMINO": "termino",
    "TOTAL": "total",
}
COLUMNAS_OPCIONALES = {
    "STATUS": "status",
    "DESCRIPCION": "descripcion",
}

# Orden de las columnas en el reporte del sistema, para tablas sin encabezado
COLUMNAS_SIN_ENCABEZADO = 18
POSICIONES_SIN_ENCABEZADO = {
    "rpe": 0,
    "laborado": 3,
    "inicio": 4,
    "termino": 5,
    "total": 6,
    "descripcion": 12,
    "status": 17,
}

PATRON_RPE = re.compile(r"[0-9A-Z]+")
PATRON_FECHA_DMY = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
PATRON_FECHA_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
FECHA_BASE_EXCEL = date(1899, 12, 30)


def importar_registros(
    archivos: list[UploadFile], textos: list[str]
) -> list[RegistroHoraExtra]:
    if not archivos and not textos:
        raise ErrorImportacion("Agrega al menos un archivo o una tabla pegada.")

    errores: list[str] = []
    tablas: list[tuple[str, pd.DataFrame]] = []

    for archivo in archivos:
        origen = archivo.filename or "Archivo sin nombre"
        try:
            tablas.append((origen, leer_archivo_crudo(archivo)))
        except ErrorImportacion as error:
            errores.append(f"{origen}: {error}")

    for numero, texto in enumerate(textos, start=1):
        origen = f"Tabla pegada {numero}"
        try:
            tablas.append((origen, leer_texto_crudo(texto)))
        except ErrorImportacion as error:
            errores.append(f"{origen}: {error}")

    registros: list[RegistroHoraExtra] = []
    for origen, tabla in tablas:
        registros_tabla, errores_tabla = extraer_registros(tabla, origen)
        registros.extend(registros_tabla)
        errores.extend(errores_tabla)

    errores.extend(buscar_duplicados(registros))

    if errores:
        raise ErrorImportacion(formatear_errores(errores))

    if not registros:
        raise ErrorImportacion("No se encontraron registros de horas extras.")

    return registros


def leer_archivo_crudo(archivo: UploadFile) -> pd.DataFrame:
    extension = Path(archivo.filename or "").suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise ErrorImportacion("Formato no permitido. Usa .xlsx, .xls o .csv.")

    archivo.file.seek(0)
    contenido = archivo.file.read()

    if not contenido:
        raise ErrorImportacion("El archivo está vacío.")

    if extension == ".csv":
        return leer_csv(decodificar(contenido))

    motor = "openpyxl" if extension == ".xlsx" else "xlrd"
    try:
        return pd.read_excel(
            io.BytesIO(contenido),
            sheet_name=0,
            header=None,
            engine=motor,
            dtype=object,
            keep_default_na=False,
        )
    except Exception as error:
        raise ErrorImportacion(
            "No se pudo leer el archivo. Verifica que sea un Excel válido."
        ) from error


def leer_texto_crudo(texto: str) -> pd.DataFrame:
    if not texto.strip():
        raise ErrorImportacion("Está vacía.")

    if "\t" not in texto:
        raise ErrorImportacion(
            "No tiene columnas separadas por tabulador. Copia la tabla "
            "directamente desde el sistema o desde Excel, sin editarla."
        )

    # Solo saltos de línea: un tabulador al inicio es una primera celda vacía
    return leer_csv(texto.lstrip("\r\n"), separador="\t")


def decodificar(contenido: bytes) -> str:
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ErrorImportacion("No se pudo leer el texto del archivo (codificación).")


def leer_csv(texto: str, separador: str | None = None) -> pd.DataFrame:
    if separador is None:
        primera_linea = texto.lstrip().split("\n", 1)[0]
        separador = "\t" if "\t" in primera_linea else ","

    try:
        filas = list(csv.reader(io.StringIO(texto), delimiter=separador))
    except csv.Error as error:
        raise ErrorImportacion(
            "No se pudo leer la tabla. Revisa que esté completa."
        ) from error

    if not filas:
        raise ErrorImportacion("No contiene filas.")

    ancho = max(len(fila) for fila in filas)
    return pd.DataFrame([fila + [""] * (ancho - len(fila)) for fila in filas])


def normalizar_nombre_columna(valor: object) -> str:
    if es_vacio(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())


def ubicar_columnas(tabla: pd.DataFrame, origen: str) -> tuple[int, dict[str, int]]:
    """Devuelve la primera fila de datos y la posición de cada campo.

    Si la primera fila es el encabezado, las columnas se toman por nombre.
    Si no, se acepta sin encabezado solo cuando tiene las columnas del reporte
    del sistema y la primera fila es un registro válido.
    """
    if tabla.empty:
        raise ErrorImportacion("No contiene filas.")

    primera_fila = tabla.iloc[0]
    nombres = [normalizar_nombre_columna(v) for v in primera_fila]

    if "RPE" in nombres:
        faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in nombres]
        if faltantes:
            raise ErrorImportacion(f"Faltan las columnas: {', '.join(faltantes)}.")

        posiciones = {
            campo: nombres.index(columna)
            for columna, campo in (
                COLUMNAS_OBLIGATORIAS.items() | COLUMNAS_OPCIONALES.items()
            )
            if columna in nombres
        }
        return 1, posiciones

    if tabla.shape[1] == COLUMNAS_SIN_ENCABEZADO:
        celdas = {
            campo: primera_fila.iloc[pos]
            for campo, pos in POSICIONES_SIN_ENCABEZADO.items()
        }
        try:
            construir_registro(celdas, origen, 1)
            return 0, POSICIONES_SIN_ENCABEZADO
        except ValueError:
            pass

    raise ErrorImportacion(
        "La primera fila no es el encabezado (RPE, LABORADO, INICIO, TERMINO, "
        f"TOTAL) ni un registro válido con las {COLUMNAS_SIN_ENCABEZADO} columnas "
        "del sistema. Copia la tabla desde los encabezados."
    )


def extraer_registros(
    tabla: pd.DataFrame, origen: str
) -> tuple[list[RegistroHoraExtra], list[str]]:
    try:
        primera_fila_datos, posiciones = ubicar_columnas(tabla, origen)
    except ErrorImportacion as error:
        return [], [f"{origen}: {error}"]

    registros: list[RegistroHoraExtra] = []
    errores: list[str] = []

    for indice in range(primera_fila_datos, len(tabla)):
        valores = tabla.iloc[indice]
        if all(es_vacio(v) for v in valores):
            continue

        fila = indice + 1
        celdas = {campo: valores.iloc[pos] for campo, pos in posiciones.items()}

        try:
            registros.append(construir_registro(celdas, origen, fila))
        except ValueError as error:
            errores.append(f"{origen}, fila {fila}: {error}")

    if not registros and not errores:
        errores.append(f"{origen}: No contiene registros.")

    return registros, errores


def construir_registro(
    celdas: dict[str, object], origen: str, fila: int
) -> RegistroHoraExtra:
    problemas: list[str] = []

    def leer(campo: str, convertir, nombre: str):
        valor = celdas.get(campo)
        if es_vacio(valor):
            problemas.append(f"falta {nombre}")
            return None
        try:
            return convertir(valor)
        except ValueError:
            problemas.append(f"{nombre} inválido ({str(valor).strip()!r})")
            return None

    rpe = leer("rpe", a_rpe, "RPE")
    laborado = leer("laborado", a_fecha, "LABORADO")
    inicio = leer("inicio", a_hora_del_dia, "INICIO")
    termino = leer("termino", a_hora_del_dia, "TERMINO")
    total = leer("total", a_duracion, "TOTAL")

    if inicio is not None and termino is not None and total is not None:
        calculado = duracion_entre(inicio, termino)
        if calculado != total:
            problemas.append(
                f"TOTAL ({formatear_hhmm(total)}) no coincide con TERMINO - INICIO "
                f"({formatear_hhmm(calculado)})"
            )

    if problemas:
        raise ValueError("; ".join(problemas) + ".")

    assert rpe and laborado and inicio and termino and total is not None
    return RegistroHoraExtra(
        rpe=rpe,
        laborado=laborado,
        inicio=inicio,
        termino=termino,
        total=total,
        status=a_texto_opcional(celdas.get("status")),
        descripcion=a_texto_opcional(celdas.get("descripcion")),
        origen=origen,
        fila=fila,
    )


def buscar_duplicados(registros: list[RegistroHoraExtra]) -> list[str]:
    vistos: dict[tuple[str, date, time], RegistroHoraExtra] = {}
    errores: list[str] = []

    for registro in registros:
        clave = (registro.rpe, registro.laborado, registro.inicio)
        anterior = vistos.get(clave)
        if anterior is None:
            vistos[clave] = registro
            continue
        errores.append(
            f"{registro.origen}, fila {registro.fila}: registro repetido de "
            f"{registro.rpe} el {registro.laborado:%d/%m/%Y} a las "
            f"{registro.inicio:%H:%M} (ya está en {anterior.origen}, "
            f"fila {anterior.fila})."
        )

    return errores


def formatear_errores(errores: list[str]) -> str:
    visibles = errores[:MAXIMO_ERRORES_REPORTADOS]
    restantes = len(errores) - len(visibles)
    mensaje = "No se importó nada. Corrige lo siguiente:\n" + "\n".join(
        f"• {error}" for error in visibles
    )
    if restantes:
        mensaje += f"\n… y {restantes} errores más."
    return mensaje


def es_vacio(valor: object) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    if isinstance(valor, str) and not valor.strip():
        return True
    return valor is pd.NaT


def a_rpe(valor: object) -> str:
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    rpe = str(valor).strip().upper()
    if not PATRON_RPE.fullmatch(rpe):
        raise ValueError
    return rpe


def a_fecha(valor: object) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, (int, float)):
        return FECHA_BASE_EXCEL + timedelta(days=int(valor))

    texto = str(valor).strip()
    if coincidencia := PATRON_FECHA_DMY.match(texto):
        dia, mes, anio = coincidencia.groups()
        return date(int(anio), int(mes), int(dia))
    if coincidencia := PATRON_FECHA_ISO.match(texto):
        anio, mes, dia = coincidencia.groups()
        return date(int(anio), int(mes), int(dia))
    raise ValueError


def a_duracion(valor: object) -> timedelta:
    """Duración desde texto "3:0", time, datetime de Excel o fracción de día."""
    if isinstance(valor, datetime):
        valor = valor.time()
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if valor < 0:
            raise ValueError
        return timedelta(minutes=round(valor * 24 * 60))
    if isinstance(valor, (str, time, timedelta)):
        return convertir_duracion(valor)
    raise ValueError


def a_hora_del_dia(valor: object) -> time:
    duracion = a_duracion(valor)
    if duracion >= UN_DIA:
        raise ValueError
    segundos = int(duracion.total_seconds())
    return time(segundos // 3600, segundos % 3600 // 60, segundos % 60)


def a_texto_opcional(valor: object) -> str | None:
    if es_vacio(valor):
        return None
    return str(valor).strip()


def duracion_entre(inicio: time, termino: time) -> timedelta:
    diferencia = datetime.combine(date.min, termino) - datetime.combine(
        date.min, inicio
    )
    return diferencia if diferencia >= timedelta() else diferencia + UN_DIA


def formatear_hhmm(duracion: timedelta) -> str:
    return formatear_duracion(duracion).rsplit(":", 1)[0]
