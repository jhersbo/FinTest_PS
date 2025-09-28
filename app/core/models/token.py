import uuid
from datetime import datetime, timezone, timedelta

from starlette.requests import Request
from sqlalchemy import String, BIGINT, Integer, TIMESTAMP, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..db.session import get_session

class Base(DeclarativeBase):
    pass

class Token(Base):
    __tablename__ = "CORE_TOKEN"

    ID:Mapped[BIGINT] = mapped_column(
        BIGINT, 
        primary_key=True,
        unique=True,
        nullable=False
    )
    TOKEN:Mapped[String] = mapped_column(
        String, 
        unique=True,
        nullable=False
    )
    IP_ADDRESS:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    STATUS:Mapped[Integer] = mapped_column(
        Integer,
        nullable=False
    )
    CREATED:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    EXPIRATION:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"ID: {self.ID}\nTOKEN: {self.TOKEN}\nIP_ADDRESS: {self.IP_ADDRESS}\nSTATUS: {self.STATUS}\nCREATED: {self.CREATED}\nEXPIRATION: {self.EXPIRATION}"
    
    def is_valid(self):
        if datetime.now(tz=timezone.utc) >= self.EXPIRATION:
            return False
        return True

    ###################
    # STATIC METHODS
    ###################
    @staticmethod
    async def create(req: Request):
        """
        Creates a new token in the database for the requesting client
        """
        if not req:
            raise RuntimeError("No request to build token from.")
        
        headers = req.headers

        token = str(uuid.uuid4())
        ip = headers.get("host")
        status = -1
        created = datetime.now(timezone.utc)
        expiration = created + timedelta(days=90)

        session = await get_session()
        try:
            T = Token(
                TOKEN=token,
                IP_ADDRESS=ip,
                STATUS=status,
                CREATED=created,
                EXPIRATION=expiration
            )
            async with session.begin():
                session.add(T)
            return T
        finally:
            session.close()

    @staticmethod
    async def find_by_token(token:str):
        """
        Finds Token object by token string
        """
        session = await get_session()
        try:
            stmt = select(Token).where(Token.TOKEN == token)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()
    ###################
    # END STATIC METHODS
    ###################