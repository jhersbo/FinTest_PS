import asyncio
from app.batch.job import Job
from app.batch.models.job_unit import JobUnit
from app.ml.core.models.model_type import ModelType
from app.ml.core.models.training_run import RunStatus, TrainingRun

class Trainable(Job):
    """
    This is the base class for all model trainers. Trainers will implement this class
    which will contain helpful methods for training.
    """
    training_run:TrainingRun

    def __init__(self):
        super().__init__()
    
    def run(self, unit):
        """
        This method should always be called by child trainer.
        """
        super().run(unit)
        self.training_run.data = self.config
        self.training_run.gid_job_unit = unit.gid
        self.training_run.status = RunStatus.RUNNING
        self.training_run._update()


    async def create_run(self, unit:JobUnit) -> TrainingRun:
        gid_model_type = self.config.get("gid_model_type")
        model = await ModelType.find_by_gid(gid_model_type)
        t_run = await TrainingRun.create(model, unit, self.config)
        self.training_run = t_run
