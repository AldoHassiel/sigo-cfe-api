from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import literal, select
from sqlalchemy.engine import RowMapping
from sqlmodel import Session, case, col, delete, func, insert

from modulos.areas.modelo import Area
from modulos.sellos.modelo import Sello


def consultar_sellos(session: Session, dias_aviso: int) -> Sequence[RowMapping]:
    fecha = col(Sello.fechaultimomovimiento)
    hoy = datetime.now(ZoneInfo("America/Mazatlan")).date()

    tiempo_limite = case(
        (col(Sello.ultimomovimiento) == "EM", 30),
        (col(Sello.ultimomovimiento) == "MR", 7),
        else_=30,
    )

    fecha_vencimiento = fecha + tiempo_limite
    dias_restantes = fecha_vencimiento - literal(hoy)

    dias_con_sello = hoy - fecha

    estado = case(
        (dias_restantes <= 0, "vencido"),
        (dias_restantes <= dias_aviso, "proximo"),
        else_="vigente",
    )

    sello = func.substr(col(Sello.numsello), 4, 1)

    tipo = case(
        (sello == "W", "PERNO"),
        (sello == "A", "CANDADO"),
        (sello == "V", "ACERADO"),
        (sello == "G", "GRIS CAND"),
        else_=" ",
    )

    consulta = (
        select(
            col(Sello.numsello),
            col(Sello.codigosello),
            col(Sello.cvearea),
            col(Sello.ultimomovimiento),
            col(Sello.proximomovimiento),
            col(Sello.rpe),
            col(Sello.rpesimed),
            fecha,
            dias_con_sello.label("dias_con_sello"),
            estado.label("estado"),
            col(Sello.cveareasimed),
            sello.label("sello"),
            tipo.label("tipo"),
            col(Area.nombre).label("nombre_area"),
            dias_restantes.label("dias_restantes"),
        )
        .join(Area, col(Sello.cvearea) == col(Area.id))
        .order_by(fecha)
        .order_by(Sello.numsello)
    )

    return session.execute(consulta).mappings().all()


def remplazar_sellos(session: Session, datos: list[dict]) -> None:
    session.exec(delete(Sello))
    session.exec(insert(Sello), params=datos)
