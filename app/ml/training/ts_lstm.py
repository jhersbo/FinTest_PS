import asyncio
from typing import Any
import joblib
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
from torch.utils.data import Dataset, DataLoader

from app.batch.models.job_unit import JobUnit
from app.core.config.config import get_config
from app.core.utils.logger import get_logger
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
        asyncio.run(TimeSeriesLSTM.train(unit, self.config))
    
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
        y = self.data[index + self.seq_len][0] 
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

        data_set = TimeSeriesLSTM(df, ticker=config["ticker"], feature_cols=f_cols)
        data_loader = DataLoader(data_set, batch_size=32, shuffle=True)

        model = LSTMModel(input_size=len(data_set.f_cols), num_layers=5)
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001) #TODO

        total_loss = 0
        for epoch in range(epochs):
            L.info(f"Seq {epoch} of {epochs} epochs...")
            model.train()
            for x_batch, y_batch in data_loader:
                optimizer.zero_grad()
                y_pred = model(x_batch)
                loss = criterion(y_pred.squeeze(), y_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                unit.accumulate("Total loss", loss.item())
        L.info(f"Finished training with {total_loss} loss")
        unit.log(f"Finished training with {total_loss} loss")

        torch.save(model.state_dict(), f"{get_config().mdl_dir}/{TimeSeriesLSTM.NAME}_{ticker}.pth")

        return model