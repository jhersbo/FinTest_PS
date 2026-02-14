from sqlalchemy import String, JSON, BOOLEAN, select
from sqlalchemy.orm import Mapped, mapped_column

from ....core.models.entity import FindableEntity
from ....core.models.globalid import GlobalId
from ....core.db.session import transaction

class ModelType(FindableEntity):
    __tablename__ = "model_type"
    __name__ = f"{__name__}.ModelType"

    model_name:Mapped[String] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    is_available:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )
    trainer_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    predictor_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    default_config:Mapped[JSON] = mapped_column(
        JSON,
        nullable=True
    )

    @staticmethod
    async def find_by_gid(gid:int) -> "ModelType":
        async with transaction() as session:
            stmt = select(ModelType).where(ModelType.gid==gid)
            return await session.scalar(statement=stmt)

    @staticmethod
    async def create(model_name:str, trainer_name:str, predictor_name:str, default_config:dict={}, is_available:bool=True):
        M = ModelType()

        async with transaction() as session:
            gid = await GlobalId.allocate(M)
            M.gid = gid.gid
            M.model_name = model_name
            M.is_available = is_available
            M.trainer_name = trainer_name
            M.predictor_name = predictor_name
            M.default_config = default_config
            session.add(M)
            await session.flush()
            return M

    async def update(self) -> None:
        async with transaction() as session:
            session.add(self)
            await session.flush()
            return

    @staticmethod
    async def find_by_name(name:str) -> "ModelType":
        async with transaction() as session:
            stmt = select(ModelType).where(ModelType.model_name==name)
            return await session.scalar(statement=stmt)

    