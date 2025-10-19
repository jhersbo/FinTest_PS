import joblib

import torch
import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler

from ..models.lstm import LSTMModel
from ..data.models.stock_history import StockHistory
from ...core.config.config import get_config

def load_model(path:str, input_size:int) -> LSTMModel:
    model = LSTMModel(input_size=input_size)
    model.load_state_dict(torch.load(path))
    model.eval()
    return model

def prep_sequence(df:pd.DataFrame, feature_cols:list[str], seq_len:int, scaler:MinMaxScaler) -> torch.Tensor:
    values = df[feature_cols].values
    scaled = scaler.transform(values)
    seq = scaled[:seq_len]
    return torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

def predict_next_price(model, input_tensor:torch.Tensor) -> float:
    with torch.no_grad():
        output = model(input_tensor)
        return output.item()
    

async def predict(ticker:str, m:str="SimplePriceLSTM") -> float: # TODO - figure out how to make this accessible for other models?
    path = f"{get_config().mdl_dir}/SimplePriceLSTM_{ticker}.pth"
    features = ['_open', 'high', 'low', 'close', 'volume']
    seq_length = 10
    input_size = len(features)

    # Load data and scaler
    data = await StockHistory.find_by_ticker(ticker=ticker)
    df = pd.DataFrame([d.__dict__ for d in data])

    scaler:MinMaxScaler = joblib.load(f"{get_config().obj_dir}/SimplePriceLSTM_{ticker}_scaler.pkl")

    # Load model
    model = load_model(path=path, input_size=input_size)

    # Prepare input and predict
    input_tensor = prep_sequence(df, feature_cols=features, seq_len=seq_length, scaler=scaler)
    scaled_prediction = predict_next_price(model=model, input_tensor=input_tensor)

    # Invert scaling
    dummy = np.zeros((1, len(features)))
    dummy[0][features.index("_open")] = scaled_prediction
    real_prediction = scaler.inverse_transform(dummy)[0][features.index("_open")]

    return real_prediction