import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_size:int=1, hidden_size:int=64, num_layers:int=2, output_size:int=1, dropout:float=0.2):
        super().__init__()
        # Add dropout to LSTM (only applies between layers if num_layers > 1)
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        # Additional dropout layer before final linear layer
        self.dropout = nn.Dropout(dropout)
        self.linear = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        # Apply dropout before final prediction
        last_output = self.dropout(last_output)
        return self.linear(last_output)
