from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import literal, select
from sqlalchemy.engine import RowMapping
from sqlmodel import Session, case, col, delete, insert

from modulos.modelos import Area
from modulos.medidores.modelo import Medidor


def consultar_medidores(session: Session, dias_aviso: int) -> Sequence[RowMapping]:
    fecha = col(Medidor.fechaultimomovimiento)
    hoy = datetime.now(ZoneInfo("America/Mazatlan")).date()

    fecha_vencimiento = fecha + 30
    dias_restantes = fecha_vencimiento - literal(hoy)

    estado = case(
        (dias_restantes <= 0, "vencido"),
        (dias_restantes <= dias_aviso, "proximo"),
        else_="vigente",
    )

    consulta = select(
        col(Medidor.nummedidor),
        col(Medidor.rpe),
        fecha,
        col(Medidor.cvearea),
        col(Area.nombre).label("nombre_area"),
        dias_restantes.label("dias_restantes"),
        estado.label("estado"),
    ).join(Area, col(Medidor.cvearea) == col(Area.id))

    return session.execute(consulta).mappings().all()


def remplazar_medidores(session: Session, datos: list[dict]) -> None:
    session.exec(delete(Medidor))
    session.exec(insert(Medidor), params=datos)
