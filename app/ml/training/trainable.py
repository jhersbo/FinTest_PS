from app.batch.job import Job

class Trainable(Job):
    """
    This is the base class for all model trainers. Trainers will implement this class
    which will contain helpful methods for training.
    """

    def __init__(self):
        super().__init__()
    
    def run(self, unit):
        super().run(unit)