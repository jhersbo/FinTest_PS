from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BOOLEAN, TIMESTAMP, select, String, BIGINT

from app.core.db.session import get_session, get_sync_session
from app.core.models.entity import FindableEntity, Entity
from app.core.models.globalid import GlobalId


class _JobStats(Entity):
    __tablename__ = "job_stats"
    __name__ = f"{__name__}._JobStats"

    s_id:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True
    )
    gid_job_unit:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    key:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    value:Mapped[String] = mapped_column(
        String,
        nullable=False
    )

    @staticmethod
    def create(gid_job_unit:int, key:str, value:float) -> "_JobStats":
        session = get_sync_session()
        try:
            J = _JobStats(
                gid_job_unit=gid_job_unit,
                key=key,
                value=str(value)
            )
            with session.begin():
                session.add(J)
            return J
        except:
            session.rollback()
        finally:
            session.close()
    
    @staticmethod
    def find_by_job_unit(gid_job_unit:int) -> list["_JobStats"]:
        session = get_sync_session()
        try:
            stmt = select(_JobStats).where(_JobStats.gid_job_unit==gid_job_unit)
            tups = session.execute(statement=stmt)
            return [t[0] for t in tups]
        finally:
            session.close()

    def update(self) -> bool:
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
        finally:
            session.close()


class _JobLog(Entity):
    __tablename__ = "job_log"
    __name__ = f"{__name__}._JobLog"

    s_id:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True
    )
    gid_job_unit:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    msg:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    timestamp:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    def create(gid_job_unit:int, msg:str) -> "_JobLog":
        now = datetime.now(tz=timezone.utc)

        session = get_sync_session()
        try:
            J = _JobLog(
                gid_job_unit=gid_job_unit,
                msg=msg,
                timestamp=now
            )
            with session.begin():
                session.add(J)
            return J
        except:
            session.rollback()
        finally:
            session.close()
    
    @staticmethod
    def find_by_job_unit(gid_job_unit:int) -> list["_JobLog"]:
        session = get_sync_session()
        try:
            stmt = select(_JobLog).where(_JobLog.gid_job_unit==gid_job_unit)
            tups = session.execute(statement=stmt)
            return [t[0] for t in tups]
        finally:
            session.close()

    def update(self) -> bool:
        session = get_sync_session()
        try:
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
        finally:
            session.close()

class JobUnit(FindableEntity):
    __allow_unmapped__ = True

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

    # Dependent objects
    _stats:dict[str, _JobStats] = {}
    _logs:list[_JobLog] = []

    @staticmethod
    async def find_by_gid(gid:int) -> "JobUnit":
        session = await get_session()
        try:
            stmt = select(JobUnit).where(JobUnit.gid==gid)
            return session.scalar(statement=stmt)
        finally:
            await session.close()

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
            self._cleanup()
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
            self._cleanup()
            with session.begin():
                session.add(self)
            return True
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def _cleanup(self) -> bool:
        for val in self._stats.values():
            if not val.update():
                raise Exception("Update failed")
        for val in self._logs:
            if not val.update():
                raise Exception("Update failed")
        return True
        
    def log(self, msg:str) -> None:
        J = _JobLog.create(self.gid, msg=msg)
        self._logs.append(J)

    def accumulate(self, key:str, value:float) -> None:
        J = None
        if not self._stats.get(key):
            J = _JobStats.create(self.gid, key=key, value=value)
        else:
            J = self._stats[key]
            J.value = (float(J.value) + float(value))
        self._stats[key] = J

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