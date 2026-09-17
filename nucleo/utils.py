from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile

from modulos.sellos.esquemas import SelloImportacion


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
            detail="El CSV está vacío, mal formado o no tiene codificación UTF-8.",
        ) from error

    datos.columns = [str(columna).strip() for columna in datos.columns]

    return datos


def dataframe_a_sellos(
    datos: pd.DataFrame,
) -> list[SelloImportacion]:
    return [
        SelloImportacion.model_validate(fila)
        for fila in datos.to_dict(orient="records")
    ]
