import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

from starlette.requests import Request
from sqlalchemy import String, BIGINT, Integer, TIMESTAMP, select
from sqlalchemy.orm import Mapped, mapped_column

from ..db.session import get_session
from ..models.entity import Entity
from ..models.globalid import GlobalId
class TokenStatus(Enum):
    ACTIVE = 1
    DEACTIVATED = 2

class Token(Entity):
    __tablename__ = "core_token"

    id:Mapped[BIGINT] = mapped_column(
        BIGINT, 
        primary_key=True,
        unique=True,
        nullable=False
    )
    token:Mapped[String] = mapped_column(
        String, 
        unique=True,
        nullable=False
    )
    ip_address:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    status:Mapped[Integer] = mapped_column(
        Integer,
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    expiration:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    
    def is_valid(self):
        if datetime.now(tz=timezone.utc) >= self.expiration:
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
        created = datetime.now(timezone.utc)
        expiration = created + timedelta(days=90)

        session = await get_session()
        try:
            gid = await GlobalId.allocate(Token.__tablename__)
            T = Token(
                id=gid.id,
                token=token,
                ip_address=ip,
                status=TokenStatus.ACTIVE.value,
                created=created,
                expiration=expiration
            )
            async with session.begin():
                session.add(T)
            return T
        finally:
            await session.close()

    @staticmethod
    async def find_by_token(token:str):
        """
        Finds Token object by token string
        """
        session = await get_session()
        try:
            stmt = select(Token).where(Token.token == token)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()
    ###################
    # END STATIC METHODS
    ###################