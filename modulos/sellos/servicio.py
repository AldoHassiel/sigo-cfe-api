from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import literal, select
from sqlalchemy.engine import RowMapping
from sqlmodel import Session, case, col, delete, insert

from modulos.modelos import Area
from modulos.sellos.modelo import Sello


def consultar_sellos(session: Session, dias_aviso: int) -> Sequence[RowMapping]:
    fecha = col(Sello.fechaultimomovimiento)
    hoy = datetime.now(ZoneInfo("America/Mazatlan")).date()

    fecha_vencimiento = fecha + 30
    dias_restantes = fecha_vencimiento - literal(hoy)

    estado = case(
        (dias_restantes <= 0, "vencido"),
        (dias_restantes <= dias_aviso, "proximo"),
        else_="vigente",
    )

    consulta = select(
        col(Sello.numsello),
        col(Sello.rpe),
        fecha,
        col(Sello.cvearea),
        col(Area.nombre).label("nombre_area"),
        dias_restantes.label("dias_restantes"),
        estado.label("estado"),
    ).join(Area, col(Sello.cvearea) == col(Area.id))

    return session.execute(consulta).mappings().all()


def remplazar_sellos(session: Session, datos: list[dict]) -> None:
    session.exec(delete(Sello))
    session.exec(insert(Sello), params=datos)
