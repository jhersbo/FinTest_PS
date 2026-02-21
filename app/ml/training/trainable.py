from typing import Any

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

    def configure(self, gid_training_run, override:dict[str, Any]={}):
        super().configure(override)
        bad_vals = [
            "",
            [],
            None
        ]
        self.config["gid_training_run"] = gid_training_run
        for k in override.keys():
            if override[k] not in bad_vals:
                self.config[k] = override[k]
