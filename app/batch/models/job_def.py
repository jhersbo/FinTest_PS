from datetime import datetime, timezone

from sqlalchemy import String, JSON, BOOLEAN, TIMESTAMP, select
from sqlalchemy.orm import Mapped, mapped_column

from app.batch.job import Job
from app.core.db.entity_finder import EntityFinder
from app.core.models.entity import FindableEntity
from app.core.models.globalid import GlobalId
from app.core.db.session import transaction


class JobDef(FindableEntity):
    __tablename__ = "job_def"

    display_name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    default_config:Mapped[JSON] = mapped_column(
        JSON,
        nullable=False
    )
    job_class:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    enabled:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    async def find_by_gid(gid:int) -> "JobDef":
        async with transaction() as session:
            stmt = select(JobDef).where(JobDef.gid==gid)
            return await session.scalar(statement=stmt)

    @staticmethod
    async def find_by_display_name(display_name:str) -> "JobDef":
        async with transaction() as session:
            stmt = select(JobDef).where(JobDef.display_name==display_name)
            return await session.scalar(statement=stmt)

    @staticmethod
    async def find_all() -> list["JobDef"]:
        async with transaction() as session:
            stmt = select(JobDef)
            result = await session.execute(statement=stmt)
            return [r[0] for r in result]

    @staticmethod
    async def create(display_name:str, job_class:str, default_config:dict={}, enabled:bool=True) -> "JobDef":
        now = datetime.now(timezone.utc)
        J = JobDef()

        async with transaction() as session:
            gid = await GlobalId.allocate(J)
            J.gid = gid.gid
            J.display_name = display_name
            J.job_class = job_class
            J.default_config = default_config
            J.enabled = enabled
            J.created = now
            session.add(J)
            await session.flush()
            return J

    async def update(self) -> None:
        async with transaction() as session:
            session.add(self)
            await session.flush()

    def get_instance(self) -> Job:
        """
        Returns a pre-configured instance of the job_class
        """
        J = EntityFinder.resolve(self.job_class)
        inst:Job = J()
        inst.gid_job_def = self.gid
        inst.config = self.default_config
        return inst
    
