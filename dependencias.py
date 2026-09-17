from typing import Annotated

from fastapi import Depends

from nucleo.db import Session, obtener_session

SessionDep = Annotated[Session, Depends(obtener_session)]
