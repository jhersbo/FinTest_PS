from abc import ABC, abstractmethod
import torch

from app.ml.core.models.training_run import TrainingRun

class Predictable(ABC):
    training_run:TrainingRun

    def configure(self, config:dict) -> None:
        self.config = {k: v for k, v in config.items() if v is not None}
    def predict(self) -> float: ...
    
    @abstractmethod
    def __load_model__(self) -> torch.nn:...

    @abstractmethod
    def __prep_sequence__(self) -> torch.Tensor:...

    @abstractmethod
    def __predict_next__(self) -> float:...

    @classmethod
    def get_class_name(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"