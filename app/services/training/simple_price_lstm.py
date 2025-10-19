import joblib
from datetime import datetime

import pandas as pd
import numpy as np

import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler

from ..models.lstm import LSTMModel
from ..data.models.stock_history import StockHistory
from ...core.config.config import get_config
from ...core.utils.logger import get_logger

L = get_logger(__name__)

class SimplePriceLSTM(Dataset):

    def __init__(self, df:pd.DataFrame, ticker:str, seq_len:int=10, feature_cols:list[str]=None):
        self.seq_len = seq_len
        self.feature_cols = feature_cols or ['_open', 'high', 'low', 'close', 'volume']
        self.ticker = ticker

        features = df[self.feature_cols].values
        self.scaler = MinMaxScaler()
        scaled = self.scaler.fit_transform(features)
        joblib.dump(self.scaler, f"{get_config().obj_dir}/SimplePriceLSTM_{self.ticker}_scaler.pkl")
        
        self.data = torch.tensor(scaled, dtype=torch.float32)

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len][3] 
        return x, y
    
    @staticmethod
    async def load(ticker:str) -> list[StockHistory]:
        data = await StockHistory.find_by_ticker(ticker=ticker)
        return data
    
    @staticmethod
    async def train(ticker:str, num_epochs:int=20, lr:float=0.001) -> LSTMModel:
        data = await SimplePriceLSTM.load(ticker=ticker)
        data = [r.__dict__ for r in data]
        df = pd.DataFrame(data)
        data_set = SimplePriceLSTM(df, ticker=ticker)
        data_loader = DataLoader(data_set, batch_size=32, shuffle=True)

        model = LSTMModel(input_size=5)
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        for epoch in range(num_epochs):
            L.info(f"Seq {epoch} of {num_epochs} epochs...")
            model.train()
            total_loss = 0
            for x_batch, y_batch in data_loader:
                optimizer.zero_grad()
                y_pred = model(x_batch)
                loss = criterion(y_pred.squeeze(), y_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
        L.info(f"Finished training with {total_loss} loss")

        torch.save(model.state_dict(), f"{get_config().mdl_dir}/SimplePriceLSTM_{ticker}.pth")

        return model

