import joblib
from datetime import datetime
import asyncio

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler

from app.batch.models.job_unit import JobUnit
from app.ml.training.trainable import Trainable

from ..model_defs.lstm import LSTMModel
from ..data.models.stock_history import StockHistory
from ...core.config.config import get_config
from ...core.utils.logger import get_logger
from ...batch.job import Job

L = get_logger(__name__)

class Trainer(Trainable):

    def __init__(self):
        super().__init__()

    def run(self, unit) -> None:
        super().run(unit=unit)
        asyncio.run(SimplePriceLSTM.train(unit=unit, **self.config))

    def get_class_name(self):
        return f"{__name__}.Trainer"

class SimplePriceLSTM(Dataset):

    NAME = "SimplePriceLSTM"

    def __init__(self, df:pd.DataFrame, ticker:str, seq_len:int=10, feature_cols:list[str]=None):
        self.seq_len = seq_len
        self.feature_cols = feature_cols or ['_open', 'high', 'low', 'close', 'volume']
        self.ticker = ticker

        features = df[self.feature_cols].values
        self.scaler = MinMaxScaler()
        scaled = self.scaler.fit_transform(features)
        joblib.dump(self.scaler, f"{get_config().obj_dir}/{SimplePriceLSTM.NAME}_{self.ticker}_scaler.pkl")
        
        self.data = torch.tensor(scaled, dtype=torch.float32)

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx:int):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len][3] 
        return x, y
    
    @staticmethod
    async def load(ticker:str) -> list[StockHistory]:
        data = await StockHistory.find_by_ticker(ticker=ticker)
        return data
    
    @staticmethod
    async def train(unit:JobUnit, ticker:str, epochs:int=20, lr:float=0.001) -> LSTMModel:
        data = await SimplePriceLSTM.load(ticker=ticker)
        data = [r.__dict__ for r in data]
        df = pd.DataFrame(data)
        data_set = SimplePriceLSTM(df, ticker=ticker)
        data_loader = DataLoader(data_set, batch_size=32, shuffle=True)

        model = LSTMModel(input_size=len(data_set.feature_cols))
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

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
        torch.save(model.state_dict(), f"{get_config().mdl_dir}/{SimplePriceLSTM.NAME}_{ticker}.pth")
        
        return model