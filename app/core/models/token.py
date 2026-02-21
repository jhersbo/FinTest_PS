import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

from starlette.requests import Request
from sqlalchemy import String, BIGINT, Integer, TIMESTAMP, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..db.session import transaction
from ..models.entity import FindableEntity
from ..models.globalid import GlobalId
class TokenStatus(Enum):
    ACTIVE = 1
    DEACTIVATED = 2

class Token(FindableEntity):
    __tablename__ = "core_token"

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
    
    def is_valid(self) -> bool:
        if datetime.now(tz=timezone.utc) >= self.expiration:
            return False
        return True

    ###################
    # STATIC METHODS
    ###################
    @staticmethod
    async def create(req: Request) -> "Token":
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

        T = Token()
        async with transaction() as session:
            gid = await GlobalId.allocate(T)
            T.gid = gid.gid
            T.token = token
            T.ip_address = ip
            T.status = TokenStatus.ACTIVE.value
            T.created = created
            T.expiration = expiration
            session.add(T)
            await session.flush()
            return T

    @staticmethod
    async def find_by_token(token:str) -> "Token":
        """
        Finds Token object by token string
        """
        async with transaction() as session:
            stmt = select(Token).where(Token.token == token)
            return await session.scalar(statement=stmt)
    ###################
    # END STATIC METHODS
    ###################