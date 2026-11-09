from datetime import date, time, timedelta

from sqlmodel import Field, SQLModel


class RegistroHoraExtra(SQLModel, table=True):
    __tablename__ = "registro_hora_extra"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    rpe: str
    laborado: date
    inicio: time
    termino: time
    total: timedelta
    status: str | None = None
    descripcion: str | None = None
    origen: str
    fila: int
