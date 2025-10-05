from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DATE, String, DOUBLE_PRECISION, BIGINT

from ...core.db.session import get_session, batch_create

class Base(DeclarativeBase):
    pass

class StockHistory(Base):
    __tablename__ = "stock_history"

    date:Mapped[DATE] = mapped_column(
        DATE,
        nullable=False
    )
    ticker:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    open:Mapped[DOUBLE_PRECISION] = mapped_column(
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

    def __repr__(self):
        return f"date: {self.date}\nticker: {self.ticker}\nopen: {self.open}\nhigh: {self.high}\n low: {self.low}\n close: {self.close}\n volume: {self.volume}"
    
    @staticmethod
    async def batch_create(objects:list[DeclarativeBase]):
        batch_create(objects=objects)