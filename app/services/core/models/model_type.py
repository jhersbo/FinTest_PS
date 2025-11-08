from sqlalchemy import BIGINT, String, JSON, BOOLEAN, select
from sqlalchemy.orm import Mapped, mapped_column

from ....core.models.entity import Entity
from ....core.models.globalid import GlobalId
from ....core.db.session import get_session

class ModelType(Entity):
    __tablename__ = "model_type"

    id:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True,
        unique=True,
        nullable=False
    )
    model_name:Mapped[String] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    config:Mapped[JSON] = mapped_column(
        JSON,
        nullable=True
    )
    is_available:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )

    @staticmethod
    async def create(model_name:str, config:dict={}, is_available:bool=True):
        session = await get_session()
        try:
            gid = await GlobalId.allocate(ModelType.__tablename__)
            M = ModelType(
                id=gid.id,
                model_name=model_name,
                config=config,
                is_available=is_available
            )
            async with session.begin():
                session.add(M)
            return M
        finally:
            await session.close()
    
    async def update(self) -> None:
        session = await get_session()
        try:
            async with session.begin():
                session.add(self)
        finally:
            await session.close()

    @staticmethod
    async def find_by_name(name:str) -> "ModelType":
        session = await get_session()
        try:
            stmt = select(ModelType).where(ModelType.model_name==name)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()