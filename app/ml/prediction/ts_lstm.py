
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


L = get_logger(__name__)

class Predictor(Predictable):

    NAME = "TimeSeriesLSTM"

    async def predict(self):
        gid = self.training_run.gid
        config = self.config

        self.ticker = await Ticker.findByTicker(config.get("ticker"))
        self.features:list[str] = config.get("f_cols")
        self.seq_length = config.get("seq_len")
        self.artifact = config.get("artifact")
        self.num_layers = config.get("num_layers")
        self.hidden_size = config.get("hidden_size")

        self.dict_path = f"{get_config().mdl_dir}/{gid}.pth"
        self.scaler:MinMaxScaler = joblib.load(f"{get_config().obj_dir}/{gid}_scaler.pkl")
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

    def __predict_next__(self):
        with torch.no_grad():
            output:torch.Tensor = self.model(self.input_tensor)
            return output

    def __prep_sequence__(self):
        self.df = self.df.sort_values(by="date", ascending=False)
        values = self.df[self.features].values
        scaled = self.scaler.transform(values)
        seq = scaled[:self.seq_length]
        return torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

    def __load_model__(self):
        model = LSTMModel(
            input_size=self.input_size, 
            hidden_size=self.hidden_size, 
            num_layers=self.num_layers, 
            output_size=self.input_size
        )
        model.load_state_dict(torch.load(self.dict_path))
        model.eval()
        return model
