from datetime import datetime, timezone

from sqlalchemy import BIGINT, TIMESTAMP, BOOLEAN, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import get_session
from ..models.entity import Entity

class GlobalId(Entity):
    __tablename__ = "global_id"

    id:Mapped[BIGINT] = mapped_column(
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

    @staticmethod
    async def allocate(table_name:str) -> "GlobalId":
        now = datetime.now(timezone.utc)

        session = await get_session()
        try:
            G = GlobalId(
                claimed=True,
                table_name=table_name,
                created=now
            )
            async with session.begin():
                session.add(G)
            return G
        finally:
            await session.close()

