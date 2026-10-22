from collections.abc import Sequence

from sqlmodel import Session, col, select

from modulos.areas.modelo import Area


def consultar_areas(session: Session) -> Sequence[Area]:
    consulta = select(Area).order_by(col(Area.nombre))
    return session.exec(consulta).all()