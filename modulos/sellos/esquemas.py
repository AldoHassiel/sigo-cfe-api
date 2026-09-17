from datetime import date

from sqlmodel import SQLModel


class SelloImportacion(SQLModel):
    numsello: str
    rpe: str
    fechaultimomovimiento: date
    cvearea: str
