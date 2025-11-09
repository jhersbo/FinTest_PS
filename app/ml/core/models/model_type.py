from sqlalchemy import BIGINT, String, JSON, BOOLEAN, select
from sqlalchemy.orm import Mapped, mapped_column

# from ....core.models.entity import Entity
from ....core.models.entity import FindableEntity
from ....core.models.globalid import GlobalId
from ....core.db.session import get_session

class ModelType(FindableEntity):
    __tablename__ = "model_type"
    __name__ = f"{__name__}.ModelType"

    # gid:Mapped[BIGINT] = mapped_column(
    #     BIGINT,
    #     primary_key=True,
    #     unique=True,
    #     nullable=False
    # )
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
    trainer_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )

    @staticmethod
    async def find_by_gid(gid:int) -> "ModelType":
        session = await get_session()
        try:
            stmt = select(ModelType).where(ModelType.gid==gid)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()

    @staticmethod
    async def create(model_name:str, trainer_name:str, config:dict={}, is_available:bool=True):
        session = await get_session()
        try:
            M = ModelType()

            gid = await GlobalId.allocate(M)

            # M = ModelType(
            #     gid=gid.gid,
            #     model_name=model_name,
            #     config=config,
            #     is_available=is_available,
            #     trainer_name=trainer_name
            # )
            M.gid = gid.gid
            M.model_name=model_name
            M.config=config
            M.is_available = is_available
            M.trainer_name = trainer_name

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