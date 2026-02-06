import asyncio
from datetime import datetime, timezone
from typing import Any
import joblib
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
from torch.utils.data import Dataset, DataLoader

from app.batch.models.job_unit import JobUnit
from app.core.config.config import get_config
from app.core.utils.logger import get_logger
from app.ml.core.models.training_run import RunStatus
from app.ml.data.models.ticker import Ticker
from app.ml.data.models.vw_ticker_timeseries import TickerTimeseries
from app.ml.model_defs.lstm import LSTMModel
from app.ml.training.trainable import Trainable

L = get_logger(__name__)

class Trainer(Trainable):
    def __init__(self):
        super().__init__()
    
    def run(self, unit):
        super().run(unit)
        try:
            asyncio.run(TimeSeriesLSTM.train(unit, self.config))
            self.training_run.status = RunStatus.COMPLETE
        except:
            self.training_run.status = RunStatus.FAILED
            raise
        finally:
            self.training_run._update()

    def get_class_name(self):
        return f"{__name__}.Trainer"
    
class TimeSeriesLSTM(Dataset):

    NAME = "TimeSeriesLSTM"

    def __init__(self, df:pd.DataFrame, ticker:str, seq_len:int=10, feature_cols:list[str]=None):
        self.seq_len = seq_len
        self.f_cols = feature_cols
        self.ticker = ticker

        features = df[self.f_cols].values
        self.scaler = MinMaxScaler()
        scaled = self.scaler.fit_transform(features)
        joblib.dump(self.scaler, f"{get_config().obj_dir}/{TimeSeriesLSTM.NAME}_{self.ticker}_scaler.pkl")

        self.data = torch.tensor(scaled, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.data) - self.seq_len

    def __getitem__(self, index) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.data[index:index + self.seq_len]
        y = self.data[index + self.seq_len][:]
        return x, y

    @staticmethod
    async def load(config:dict[str, Any]) -> pd.DataFrame:
        ticker = await Ticker.findByTicker(config.get("ticker"))
        tts = await TickerTimeseries.findByTicker(ticker=ticker)
        return pd.DataFrame([r.__dict__ for r in tts])

    @staticmethod
    async def train(unit:JobUnit, config:dict[str, Any]) -> LSTMModel:
        df = await TimeSeriesLSTM.load(config)
        ticker = config.get("ticker")
        f_cols = config.get("f_cols")
        epochs = config.get("epochs")
        hidden_size = config.get("hidden_size")
        num_layers = config.get("num_layers")

        data_set = TimeSeriesLSTM(df, ticker=ticker, feature_cols=f_cols)
        data_loader = DataLoader(data_set, batch_size=32)

        model = LSTMModel(input_size=len(data_set.f_cols), hidden_size=hidden_size, num_layers=num_layers, output_size=len(data_set.f_cols))
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters())
        
        #stats
        epoch_losses = []

        for epoch in range(epochs):
            L.info(f"Seq {epoch} of {epochs} epochs...")
            epoch_loss = 0
            model.train()
            for x_batch, y_batch in data_loader:
                optimizer.zero_grad()
                y_pred = model(x_batch)
                loss:torch.Tensor = criterion(y_pred, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            mean_loss = epoch_loss / len(data_loader)
            L.info(f"Epoch {epoch} mean loss: {mean_loss}")
            epoch_losses.append(mean_loss)

            # TODO - set up a validation split

        torch.save(model.state_dict(), f"{get_config().mdl_dir}/{TimeSeriesLSTM.NAME}_{ticker}.pth")

        return model