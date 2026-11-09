from sqlalchemy import Date, cast, func
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlmodel import Session, col, delete, select

from .modelo import RegistroHoraExtra


def consultar_horas_extras(session: Session, limite_horas_semanales: float):
    # Semana de lunes a domingo a la que pertenece cada registro
    semana = func.date_trunc("week", col(RegistroHoraExtra.laborado))

    horas_por_semana = (
        select(
            col(RegistroHoraExtra.rpe).label("rpe"),
            cast(semana, Date).label("semana"),
            func.sum(col(RegistroHoraExtra.total)).label("horas"),
        )
        .group_by(col(RegistroHoraExtra.rpe), semana)
        .subquery()
    )

    # Semanas del periodo importado; un RPE sin registros en una semana
    # cuenta esa semana con 0 horas
    total_semanas = select(func.count(func.distinct(semana))).scalar_subquery()

    semana_excedida = (
        func.extract("epoch", horas_por_semana.c.horas) > limite_horas_semanales * 3600
    )
    semanas_excedidas = func.count().filter(semana_excedida)

    # Detalle de cada semana del RPE, para filtrar por semana en el frontend
    detalle_semanas = func.json_agg(
        aggregate_order_by(
            func.json_build_object(
                "semana",
                horas_por_semana.c.semana,
                "horas",
                horas_por_semana.c.horas,
                "excede_limite_semanal",
                semana_excedida,
            ),
            horas_por_semana.c.semana,
        )
    )

    consulta = (
        select(
            horas_por_semana.c.rpe,
            func.sum(horas_por_semana.c.horas).label("horas_totales"),
            semanas_excedidas.label("semanas_excedidas"),
            total_semanas.label("total_semanas"),
            (semanas_excedidas > 0).label("excede_limite_semanal"),
            detalle_semanas.label("semanas"),
        )
        .group_by(horas_por_semana.c.rpe)
        .order_by(horas_por_semana.c.rpe)
    )

    return session.execute(consulta).mappings().all()


def remplazar_registros_horas_extras(
    session: Session, registros: list[RegistroHoraExtra]
) -> None:
    session.exec(delete(RegistroHoraExtra))
    session.add_all(registros)
