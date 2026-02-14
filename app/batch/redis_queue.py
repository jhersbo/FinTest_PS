from redis import Redis
from rq import Queue
from rq.job import Job as rqJob

from app.batch.models.job_unit import JobUnit
from app.core.config.config import get_config
from app.core.db.session import transaction
from app.core.utils.logger import get_logger

from .job import Job

L = get_logger(__name__)

class RedisQueue:
    REDIS_PORT = get_config().redis_port
    REDIS_SERVICE = "redis"
    QUEUE_CACHE = {
        "long": None,
        "short": None
    }
    DEFAULT_TIMEOUT = 100000

    def __init__(self, queue: Queue):
        self.Q:Queue = queue

    async def put(self, job:Job) -> rqJob:
        async with transaction():
            unit = await JobUnit.create()
            _job = self.Q.enqueue(job.run, args=(unit,), job_timeout=RedisQueue.DEFAULT_TIMEOUT, on_success=end, on_failure=fail, meta={"gid_job_unit": unit.gid})
            unit.rq_token = _job.id
            await unit.update()
            return _job
        return None

    @staticmethod
    def get_queue(name) -> "RedisQueue":
        if not RedisQueue.QUEUE_CACHE.get(name):
            conn = RedisQueue.__connection__()
            Q = Queue(connection=conn, name=name)
            RQ = RedisQueue(Q)
            RedisQueue.QUEUE_CACHE[Q.name] = RQ
            return RQ
        return RedisQueue.QUEUE_CACHE.get(name)
    
    @staticmethod
    def find_job(rq_token:str) -> rqJob:
        return rqJob.fetch(rq_token, connection=RedisQueue.__connection__())

    @staticmethod
    def __connection__() -> Redis:
        return Redis(RedisQueue.REDIS_SERVICE, RedisQueue.REDIS_PORT, db=0)

def end(job:rqJob, *args, **kwargs) -> None:
    # TODO - maybe we add job logs here
    unit = JobUnit._find_by_gid(job.meta["gid_job_unit"])
    if not unit.end_job():
        raise

def fail(job:rqJob, *args, **kwargs) -> None:
    # TODO - maybe we add job logs here
    unit = JobUnit._find_by_gid(job.meta["gid_job_unit"])
    if not unit.fail_job():
        raise
