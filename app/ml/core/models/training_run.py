from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import BIGINT, String, JSON, TIMESTAMP, select
from sqlalchemy.orm import Mapped, mapped_column

from ....core.db.session import get_session
# from ....core.models.entity import Entity
from ....core.models.entity import FindableEntity
from ....core.models.globalid import GlobalId
from .model_type import ModelType

class RunStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


class TrainingRun(FindableEntity):
    __tablename__ = "training_run"
    __name__ = f"{__name__}.TrainingRun"

    id_model_type:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    start:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    end:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    data:Mapped[JSON] = mapped_column(
        JSON,
        nullable=False
    )
    status:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    async def create(model:ModelType) -> "TrainingRun":
        if not model:
            raise RuntimeError("No model given")
        
        now = datetime.now(timezone.utc)

        session = await get_session()
        try:
            T = TrainingRun()

            gid = await GlobalId.allocate(T)
            T.gid = gid.gid
            T.id_model_type = model.id
            T.start = None
            T.end = None
            T.data = {}
            T.status = RunStatus.PENDING
            T.created  = now

            async with session.begin():
                session.add(T)
            return T
        finally:
            await session.close()

    async def update(self) -> None:
        session = await get_session()
        try:
            async with session.begin():
                session.add(self)
        finally:
            await session.close()

    @staticmethod
    async def find_by_id(id:int) -> "TrainingRun":
        session = await get_session()
        try:
            stmt = select(TrainingRun).where(TrainingRun.id==id)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()
    
    @staticmethod
    async def find_by_model(model:ModelType) -> list["TrainingRun"]:
        session = await get_session()
        try:
            stmt = select(TrainingRun).where(TrainingRun.id_model_type==model.id)
            tups = await session.execute(statement=stmt)
            result = []
            for t in tups:
                result.append(t[0])
            return result
        finally:
            await session.close()
