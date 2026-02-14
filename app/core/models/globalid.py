from datetime import datetime, timezone

from sqlalchemy import BIGINT, TIMESTAMP, BOOLEAN, String, select
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import transaction
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
    class_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    async def find_by_gid(gid:int) -> "GlobalId":
        async with transaction() as session:
            stmt = select(GlobalId).where(GlobalId.gid==gid)
            return await session.scalar(statement=stmt)

    @staticmethod
    async def allocate(entity:FindableEntity) -> "GlobalId":
        now = datetime.now(timezone.utc)
        G = GlobalId(
            claimed=True,
            table_name=entity.__tablename__,
            created=now,
            class_name=entity.get_name()
        )
        async with transaction() as session:
            session.add(G)
            await session.flush()
            return G

