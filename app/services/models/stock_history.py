from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DATE, String, DOUBLE_PRECISION, BIGINT

from ...core.db.session import get_session, batch_create
from ...core.models.entity import Entity

class StockHistory(Entity):
    __tablename__ = "stock_history"

    decode:Mapped[String] = mapped_column(
        String,
        nullable=False,
        primary_key=True
    )
    date:Mapped[DATE] = mapped_column(
        DATE,
        nullable=False
    )
    ticker:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    _open:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    high:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    low:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    close:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    volume:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )

    @staticmethod
    async def batch_create(objects:list["StockHistory"]) -> int:
        return await batch_create(objects=objects)