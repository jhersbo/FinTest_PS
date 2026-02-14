from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BIGINT, String, JSON, TIMESTAMP, select
from sqlalchemy.orm import Mapped, mapped_column

from app.batch.models.job_unit import JobUnit
from app.ml.core.models.model_type import ModelType

from ....core.db.session import get_session, get_sync_session, current_session, transaction
from ....core.models.entity import FindableEntity
from ....core.models.globalid import GlobalId

class RunStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class TrainingRun(FindableEntity):
    __tablename__ = "training_run"
    __name__ = f"{__name__}.TrainingRun"

    gid_model_type:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    gid_job_unit:Mapped[BIGINT] = mapped_column(
        BIGINT
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
    async def create(model:ModelType, unit:JobUnit=None, data:dict[str, Any]={}) -> "TrainingRun":
        if not model:
            raise RuntimeError("No model given")

        now = datetime.now(timezone.utc)
        T = TrainingRun()

        async with transaction() as session:
            gid = await GlobalId.allocate(T)
            T.gid = gid.gid
            T.gid_model_type = model.gid
            T.gid_job_unit = unit.gid if unit else None
            T.data = data
            T.status = RunStatus.PENDING
            T.created = now
            session.add(T)
            await session.flush()
            return T

    async def update(self) -> None:
        async with transaction() as session:
            session.add(self)
            await session.flush()

    def _update(self) -> None:
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
        finally:
            session.close()

    @staticmethod
    async def find_by_id(gid:int) -> "TrainingRun":
        async with transaction() as session:
            stmt = select(TrainingRun).where(TrainingRun.gid==gid)
            return await session.scalar(statement=stmt)

    @staticmethod
    async def find_by_model(gid_model_type:int) -> list["TrainingRun"]:
        async with transaction() as session:
            stmt = select(TrainingRun).where(TrainingRun.gid_model_type==gid_model_type)
            tups = await session.execute(statement=stmt)
            return [t[0] for t in tups]
