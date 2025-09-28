from sqlalchemy import String, BIGINT, Integer, TIMESTAMP, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..db.session import get_session

class Base(DeclarativeBase):
    pass

class Token(Base):
    __tablename__ = "CORE_TOKEN"

    ID:Mapped[BIGINT]=mapped_column(BIGINT, primary_key=True)
    TOKEN:Mapped[String]=mapped_column(String)
    IP_ADDRESS:Mapped[String]=mapped_column(String)
    STATUS:Mapped[Integer]=mapped_column(Integer)
    TS:Mapped[TIMESTAMP]=mapped_column(TIMESTAMP)

    def __repr__(self) -> str:
        return f"ID: {self.ID}\nTOKEN: {self.TOKEN}\nIP_ADDRESS: {self.IP_ADDRESS}\nSTATUS: {self.STATUS}\nTS: {self.TS}"
    
    @staticmethod
    async def find_by_token(token:str):
        session = await get_session()
        try:
            stmt = select(Token).where(Token.TOKEN.in_([token]))
            return await session.scalar(statement=stmt)
        finally:
            await session.close()