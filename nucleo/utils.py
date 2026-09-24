from pathlib import Path
from datetime import UTC, datetime, timedelta, timezone
import pandas as pd
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, ValidationError

from nucleo.errores import ErrorImportacion


def leer_archivo(archivo: UploadFile) -> pd.DataFrame:
    extension = Path(archivo.filename or "").suffix.lower()

    if extension not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Usa CSV, XLSX o XLS.",
        )

    archivo.file.seek(0)

    try:
        if extension == ".csv":
            datos = pd.read_csv(
                archivo.file,
                sep=",",
                encoding="utf-8-sig",
                dtype=str,
                keep_default_na=False,
            )
        else:
            motor = "openpyxl" if extension == ".xlsx" else "xlrd"

            datos = pd.read_excel(
                archivo.file,
                sheet_name=0,
                engine=motor,
                dtype=object,
                keep_default_na=False,
            )

    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer el archivo. Revisa su formato y contenido",
        ) from error

    datos.columns = [str(columna).strip() for columna in datos.columns]

    return datos


def validar_datos(
    datos: pd.DataFrame, esquema: type[BaseModel], clave_unica: str | None = None
) -> list[dict]:
    if datos.empty:
        raise ErrorImportacion("El archivo no contiene registros.")

    if datos.columns.duplicated().any():
        raise ErrorImportacion("Hay encabezados repetidos.")

    obligatorios = {
        nombre for nombre, campo in esquema.model_fields.items() if campo.is_required()
    }

    faltantes = obligatorios - set(datos.columns)

    if faltantes:
        raise ErrorImportacion(f"Faltan columnas: {','.join(sorted(faltantes))}")

    campos = [nombre for nombre in esquema.model_fields if nombre in datos.columns]

    filas = []
    identificadores = set()

    for numero, valores in enumerate(
        datos[campos].itertuples(index=False, name=None), start=2
    ):
        try:
            registro = esquema.model_validate(dict(zip(campos, valores))).model_dump()
        except ValidationError as error:
            campos_invalidos = ", ".join(
                ".".join(str(parte) for parte in detalle["loc"])
                for detalle in error.errors()
            )
            raise ErrorImportacion(
                f"Fila {numero}: formato inválido en {campos_invalidos}."
            ) from error

        if clave_unica is not None:
            identificador = registro[clave_unica]

            if identificador in identificadores:
                raise ErrorImportacion("Hay identificadores repetidos")

            identificadores.add(identificador)

        filas.append(registro)

    return filas


def convertir_a_time(hora_string: str):
    hora_convertida = datetime.strptime(hora_string, "%H:%M:%S").time()
    return hora_convertida
