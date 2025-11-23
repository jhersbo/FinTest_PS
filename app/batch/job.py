from app.batch.models.job_unit import JobUnit


class Job:
    config:dict[str, str] = {}

    def run(self, unit:JobUnit) -> None:
        unit.start_job()

    def configure(self, config:dict) -> None:
        self.config = config

    def get_class_name(self) -> str:
        raise NotImplementedError("Child must implement this method")