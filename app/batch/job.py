
from datetime import datetime, timezone
from typing import Any
from app.batch.models.job_unit import JobUnit
from app.core.utils.serializable import Serializable


class Job(Serializable):
    """
    This is the base class for all jobs consumed by the Redis queue.
    To create a new job, one must create a class which inherits from this one:
    ```python
    class MyJob(Job):
        def __init__(self):
            super().__init__()
        def run(self, unit:JobUnit):
            self.run(unit)
            ...
    """
    gid_job_def:int
    config:dict[str, Any] = {}

    def run(self, unit:JobUnit) -> None:
        unit.start_job()

    async def _run(self, unit:JobUnit) -> None:
        """
        This method can be implemented for async behavior in jobs
        """
        raise NotImplementedError("Child must implement this method")

    def configure(self, config:dict[str, Any]) -> None:
        """
        Merges a dict with this job's config dict, prioritizing the properties given in the argument
        """
        for k in config.keys():
            self.config[k] = config[k]
    
    @staticmethod
    def now() -> datetime:
        """
        Can use this method for job timestamps when needed
        :return: Datetime object for now
        :rtype: datetime
        """
        return datetime.now(timezone.utc)
    
    @classmethod
    def get_class_name(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"