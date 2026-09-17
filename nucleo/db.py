from sqlmodel import Session, SQLModel, create_engine

from nucleo.config import config

engine = create_engine(config.db_url, echo=False)


def crear_tablas():
    import modulos.modelos  # noqa: F401

    SQLModel.metadata.create_all(engine)


async def obtener_session():
    with Session(engine) as session:
        yield session
