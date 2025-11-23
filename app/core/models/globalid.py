from datetime import datetime, timezone

from sqlalchemy import BIGINT, TIMESTAMP, BOOLEAN, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..db.session import get_session
from ..models.entity import Entity
from ..models.entity import FindableEntity

class GlobalId(Entity):
    __tablename__ = "global_id"

    gid:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True,
        unique=True,
        nullable=False
    )
    claimed:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )
    table_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    class_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )

    @staticmethod
    async def find_by_gid(gid:int) -> "GlobalId":
        session = await get_session()
        try:
            stmt = select(GlobalId).where(GlobalId.gid==gid)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()

    @staticmethod
    async def allocate(entity:FindableEntity) -> "GlobalId":
        now = datetime.now(timezone.utc)

        session = await get_session()
        try:
            G = GlobalId(
                claimed=True,
                table_name=entity.__tablename__,
                created=now,
                class_name=entity.get_name()
            )
            async with session.begin():
                session.add(G)
            return G
        finally:
            await session.close()

