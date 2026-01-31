
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
from app.core.config.config import get_config
from app.core.utils.logger import get_logger
from app.ml.data.models.ticker import Ticker
from app.ml.data.models.vw_ticker_timeseries import TickerTimeseries
from app.ml.model_defs.lstm import LSTMModel
from app.ml.prediction.predictable import Predictable


L = get_logger()

class Predictor(Predictable):

    """
    Config structured as follows:

    ```python
    {
        features:list[str],
        seq_length:int,
        artifact:str
    }
    """

    NAME = "TimeSeriesLSTM"

    async def predict(self):
        self.ticker = await Ticker.findByTicker(self.config.get("ticker"))
        self.features:list[str] = self.config.get("features")
        self.seq_length = self.config.get("seq_length")
        self.artifact = self.config.get("artifact")

        self.dict_path = f"{get_config().mdl_dir}/{Predictor.NAME}_{self.ticker.ticker}.pth"
        self.scaler:MinMaxScaler = joblib.load(f"{get_config().obj_dir}/{Predictor.NAME}_{self.ticker.ticker}_scaler.pkl")
        self.input_size = len(self.features)

        self.data = await TickerTimeseries.findByTicker(self.ticker)
        self.df = pd.DataFrame([r.__dict__ for r in self.data])

        self.model = self.__load_model__()
        self.input_tensor = self.__prep_sequence__()
        scaled_prediction = self.__predict_next__()

        dummy = np.zeros((1, len(self.features)))
        artifact_index = self.features.index(self.artifact)
        dummy[0][artifact_index] = scaled_prediction[0][artifact_index].item()
        return self.scaler.inverse_transform(dummy)[0][artifact_index]
    
    def get_class_name(self):
        return f"{__name__}.Predictor"

    def __predict_next__(self):
        with torch.no_grad():
            output:torch.Tensor = self.model(self.input_tensor)
            return output
    
    def __prep_sequence__(self):
        values = self.df[self.features].values
        scaled = self.scaler.transform(values)
        seq = scaled[0:self.seq_length]
        return torch.tensor(seq, dtype=torch.float32).unsqueeze(0)
    
    def __load_model__(self):
        model = LSTMModel(input_size=self.input_size, output_size=self.input_size)
        model.load_state_dict(torch.load(self.dict_path))
        model.eval()
        return model
