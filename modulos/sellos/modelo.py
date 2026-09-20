from datetime import date

from sqlmodel import Field, SQLModel


class Sello(SQLModel, table=True):
    numsello: str = Field(primary_key=True)
    rpe: str
    fechaultimomovimiento: date

    cvearea: str = Field(foreign_key="area.id")
