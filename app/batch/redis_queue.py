from redis import Redis
from rq import Queue, Callback
from rq.job import Job as rqJob

from app.batch.models.job_unit import JobUnit

from .job import Job

class RedisQueue:
    REDIS_PORT = 6379
    REDIS_SERVICE = "redis"
    QUEUE_CACHE = {
        "seeder": None,
        "trainer": None
    }
    DEFAULT_TIMEOUT = 1000

    def __init__(self, queue: Queue):
        self.Q:Queue = queue

    async def put(self, job:Job) -> rqJob:
        unit = await JobUnit.create()
        _job = self.Q.enqueue(job.run, args=(unit,), job_timeout=RedisQueue.DEFAULT_TIMEOUT, on_success=end, on_failure=fail)
        _job.meta["gid_job_unit"] = unit.gid
        _job.save()
        return _job

    @staticmethod
    def get_queue(name:str="default") -> "RedisQueue":
        if not RedisQueue.QUEUE_CACHE.get(name):
            conn = Redis(RedisQueue.REDIS_SERVICE, RedisQueue.REDIS_PORT, db=0)
            Q = Queue(connection=conn, name=name)
            RQ = RedisQueue(Q)
            RedisQueue.QUEUE_CACHE[Q.name] = RQ
            return RQ
        return RedisQueue.QUEUE_CACHE.get(name)

def end(job:rqJob, connection, result, *args, **kwargs) -> None:
    # TODO - maybe we add job logs here
    unit = JobUnit._find_by_gid(job.meta["gid_job_unit"])
    if not unit.end_job():
        raise

def fail(job:rqJob, connection, type, traceback) -> None:
    # TODO - maybe we add job logs here
    unit = JobUnit._find_by_gid(job.meta["gid_job_unit"])
    if not unit.fail_job():
        raise
