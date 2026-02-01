
from app.core.db.entity_finder import EntityFinder
from app.ml.core.models.model_type import ModelType
from app.ml.prediction.predictable import Predictable
from app.ml.training.trainable import Trainable


class ModelFacade():
    """
    This is a facade class used for retrieving objects
    used in models/training/prediction, etc...
    """
    @staticmethod
    def trainer_for(model:ModelType) -> Trainable:
        """
        Docstring for trainer_for
        
        :param model:
        :type model: ModelType
        :return: Instance of the model's trainer class
        :rtype: Trainable
        """
        c = EntityFinder.resolve(model.trainer_name)
        return c()
    
    @staticmethod
    def predictor_for(model:ModelType) -> Predictable:
        """
        Docstring for predictor_for
        
        :param model:
        :type model: ModelType
        :return: Instance of the model's predictor class
        :rtype: Predictable
        """
        c = EntityFinder.resolve(model.predictor_name)
        return c()
    