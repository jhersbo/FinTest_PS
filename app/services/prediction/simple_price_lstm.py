import joblib

import torch
import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler

from ..models.lstm import LSTMModel
from ..data.models.stock_history import StockHistory
from ...core.config.config import get_config

def __load_model__(path:str, input_size:int) -> LSTMModel:
    model = LSTMModel(input_size=input_size)
    model.load_state_dict(torch.load(path))
    model.eval()
    return model

def __prep_sequence__(df:pd.DataFrame, feature_cols:list[str], seq_len:int, scaler:MinMaxScaler) -> torch.Tensor:
    values = df[feature_cols].values
    scaled = scaler.transform(values)
    seq = scaled[:seq_len]
    return torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

def __predict_next__(model, input_tensor:torch.Tensor) -> float:
    with torch.no_grad():
        output = model(input_tensor)
        return output.item()
    
async def predict(ticker:str, seq_length:int, artifact:str) -> float: # TODO - figure out how to make this accessible for other models?
    path = f"{get_config().mdl_dir}/SimplePriceLSTM_{ticker}.pth"
    features = ['_open', 'high', 'low', 'close', 'volume']
    input_size = len(features)

    # Load data and scaler
    data = await StockHistory.find_by_ticker(ticker=ticker)
    df = pd.DataFrame([d.__dict__ for d in data])

    scaler:MinMaxScaler = joblib.load(f"{get_config().obj_dir}/SimplePriceLSTM_{ticker}_scaler.pkl")
    # scaler:MinMaxScaler = MinMaxScaler()
    # scaler.fit(df[features].values)

    # Load model
    model = __load_model__(path=path, input_size=input_size)

    # Prepare input and predict
    input_tensor = __prep_sequence__(df, feature_cols=features, seq_len=seq_length, scaler=scaler)
    scaled_prediction = __predict_next__(model=model, input_tensor=input_tensor)

    # Invert scaling
    dummy = np.zeros((1, len(features)))
    dummy[0][features.index(artifact)] = scaled_prediction
    real_prediction = scaler.inverse_transform(dummy)[0][features.index(artifact)]

    return real_prediction