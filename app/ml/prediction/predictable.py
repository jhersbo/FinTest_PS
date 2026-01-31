import torch

class Predictable():
    def configure(self, config:dict) -> None:
        self.config = {k: v for k, v in config.items() if v is not None}
    def predict(self) -> float: ...
    def __load_model__(self) -> torch.nn:
        raise NotImplementedError("Child must implement this method")
    def __prep_sequence__(self) -> torch.Tensor:
        raise NotImplementedError("Child must implement this method")
    def __predict_next__(self) -> float:
        raise NotImplementedError("Child must implement this method")
    def get_class_name() -> str:
        raise NotImplementedError("Child must implement this method")