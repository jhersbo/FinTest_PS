import asyncio
import inspect
from typing import Callable, Coroutine, Any

from redis import Redis
from rq import Queue
from rq.job import Job as rqJob

from .job import Job

class RedisQueue:
    # 'Static' properties
    REDIS_PORT = 6379
    REDIS_SERVICE = "redis"
    QUEUE_CACHE = {}
    DEFAULT_TIMEOUT = 1000

    def __init__(self, queue: Queue):
        self.Q:Queue = queue

    def put(self, job:Job) -> rqJob:
        return self.Q.enqueue(job.run, args=(), job_timeout=RedisQueue.DEFAULT_TIMEOUT)

    @staticmethod
    def get_queue(name:str="default") -> "RedisQueue":
        if not RedisQueue.QUEUE_CACHE.get(name):
            conn = Redis(RedisQueue.REDIS_SERVICE, RedisQueue.REDIS_PORT, db=0)
            Q = Queue(connection=conn, name=name)
            RQ = RedisQueue(Q)
            RedisQueue.QUEUE_CACHE[Q.name] = RQ
            return RQ
        return RedisQueue.QUEUE_CACHE.get(name)

async def __async_wrapper__(fn, *args, **kwargs):
    return await fn(*args, **kwargs)