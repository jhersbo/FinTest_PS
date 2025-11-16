from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BOOLEAN, TIMESTAMP, select

from app.core.db.session import get_session, get_sync_session
from app.core.models.entity import FindableEntity
from app.core.models.globalid import GlobalId

class JobUnit(FindableEntity):
    __tablename__ = "job_unit"
    __name__ = f"{__name__}.JobUnit"

    failed:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )
    ack:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    start:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    end:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True)
    )

    @staticmethod
    def _find_by_gid(gid:int) -> "JobUnit":
        session = get_sync_session()
        try:
            stmt = select(JobUnit).where(JobUnit.gid==gid)
            return session.scalar(statement=stmt)
        finally:
            session.close()

    def start_job(self) -> bool:
        self.start = datetime.now(timezone.utc)
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def end_job(self) -> bool:
        self.end = datetime.now(timezone.utc)
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def fail_job(self) -> bool:
        self.end = datetime.now(timezone.utc)
        self.failed = True
        self.ack = False
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    async def create() -> "JobUnit":
        now = datetime.now(timezone.utc)
        session = await get_session()
        try:
            J = JobUnit()

            gid = await GlobalId.allocate(J)
            J.gid = gid.gid
            J.failed = False
            J.ack = None
            J.created = now
            J.start = None
            J.end = None

            async with session.begin():
                session.add(J)
            return J
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
