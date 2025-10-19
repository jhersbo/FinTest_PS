import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_size:int=1, hidden_size:int=64, num_layers:int=2, output_size:int=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_ouput = lstm_out[:, -1, :]
        return self.linear(last_ouput)
