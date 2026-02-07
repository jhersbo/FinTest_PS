# LSTM Training Parameters Documentation

**Last Updated**: 2026-02-06
**Model**: TimeSeriesLSTM
**Files**: `app/ml/training/ts_lstm.py`, `app/ml/model_defs/lstm.py`

---

## Overview

This document describes all configurable parameters for training the LSTM time series prediction model. The training process includes train/validation splitting, early stopping, learning rate scheduling, gradient clipping, and comprehensive metrics tracking.

---

## Required Parameters

### `ticker` (string)
- **Description**: Stock ticker symbol to train on
- **Example**: `"AAPL"`, `"TSLA"`, `"MSFT"`
- **Required**: Yes

### `f_cols` (list of strings)
- **Description**: List of feature column names to use for training
- **Available Features**:
  - `"open"` - Opening price
  - `"high"` - High price
  - `"low"` - Low price
  - `"close"` - Closing price
  - `"volume"` - Trading volume
  - `"sma_value"` - Simple moving average
- **Example**: `["open", "high", "low", "close", "volume", "sma_value"]`
- **Required**: Yes
- **Notes**:
  - All features are scaled together using MinMaxScaler
  - Model predicts all input features (multi-output)
  - Ensure features exist in the database view `vw_ticker_timeseries`

---

## Model Architecture Parameters

### `hidden_size` (integer)
- **Description**: Number of features in the hidden state of the LSTM
- **Default**: `64`
- **Typical Range**: `32` to `512`
- **Recommended**:
  - Small datasets (< 1000 samples): `64`
  - Medium datasets (1000-5000 samples): `128`
  - Large datasets (> 5000 samples): `256` or `512`
- **Impact**:
  - Larger values increase model capacity but require more data
  - May lead to overfitting on small datasets

### `num_layers` (integer)
- **Description**: Number of stacked LSTM layers
- **Default**: `2`
- **Typical Range**: `1` to `4`
- **Recommended**:
  - Simple patterns: `1` or `2`
  - Complex patterns: `3` or `4`
- **Impact**:
  - More layers can capture more complex temporal patterns
  - Increases training time and memory usage
  - Diminishing returns after 3-4 layers

### `dropout` (float)
- **Description**: Dropout probability for regularization
- **Default**: `0.2`
- **Range**: `0.0` to `0.5`
- **Recommended**:
  - No regularization: `0.0`
  - Light regularization: `0.1` to `0.2`
  - Moderate regularization: `0.3`
  - Heavy regularization: `0.4` to `0.5`
- **Impact**:
  - Prevents overfitting by randomly dropping connections during training
  - Too high can lead to underfitting
  - Applied between LSTM layers (if num_layers > 1) and before final linear layer
- **Notes**: Only active during training, automatically disabled during inference

---

## Training Loop Parameters

### `epochs` (integer)
- **Description**: Maximum number of training epochs
- **Default**: `100`
- **Typical Range**: `50` to `500`
- **Recommended**:
  - Quick experiments: `20` to `50`
  - Full training: `100` to `200`
  - Deep tuning: `200` to `500`
- **Impact**:
  - More epochs allow better convergence but increase training time
  - Early stopping will terminate training before max epochs if validation loss stops improving
- **Notes**: With early stopping (patience=15), actual training typically stops around 30-80 epochs

### `batch_size` (integer)
- **Description**: Number of sequences processed in each training batch
- **Default**: `64`
- **Typical Range**: `16` to `256`
- **Recommended**:
  - Small datasets: `16` or `32`
  - Medium datasets: `64` or `128`
  - Large datasets: `128` or `256`
  - GPU memory limited: reduce until fits
- **Impact**:
  - Larger batches provide more stable gradients but use more memory
  - Smaller batches add noise that can help escape local minima
  - Must be smaller than training dataset size

### `learning_rate` (float)
- **Description**: Initial learning rate for Adam optimizer
- **Default**: `0.001`
- **Typical Range**: `0.0001` to `0.01`
- **Recommended**:
  - Conservative (stable): `0.0001` to `0.0005`
  - Moderate (default): `0.001`
  - Aggressive (faster convergence): `0.005` to `0.01`
- **Impact**:
  - Higher rates converge faster but may overshoot optimal weights
  - Lower rates are more stable but slower to converge
  - Learning rate scheduler will reduce this by 50% when validation loss plateaus
- **Notes**: Reduced automatically during training by ReduceLROnPlateau scheduler

### `weight_decay` (float)
- **Description**: L2 regularization coefficient (weight decay)
- **Default**: `1e-5` (0.00001)
- **Typical Range**: `0` to `1e-3`
- **Recommended**:
  - No regularization: `0`
  - Light regularization: `1e-5` to `1e-4`
  - Strong regularization: `1e-3`
- **Impact**:
  - Penalizes large weights to prevent overfitting
  - Acts as an additional form of regularization alongside dropout
  - Too high can lead to underfitting

---

## Validation & Early Stopping Parameters

### `train_split` (float)
- **Description**: Fraction of data to use for training (remainder used for validation)
- **Default**: `0.8` (80% train, 20% validation)
- **Typical Range**: `0.7` to `0.9`
- **Recommended**:
  - Small datasets (< 500 samples): `0.7` to `0.75`
  - Medium datasets: `0.8`
  - Large datasets (> 5000 samples): `0.85` to `0.9`
- **Impact**:
  - Higher values give more training data but less reliable validation metrics
  - Lower values provide better validation estimates but less training data
- **Notes**:
  - Split is performed temporally (oldest data = train, newest = validation)
  - NO shuffling is performed (maintains time series order)

### `patience` (integer)
- **Description**: Number of epochs to wait for validation improvement before early stopping
- **Default**: `15`
- **Typical Range**: `5` to `30`
- **Recommended**:
  - Fast experimentation: `5` to `10`
  - Standard training: `15` to `20`
  - Patient training: `25` to `30`
- **Impact**:
  - Higher patience allows more time to escape plateaus
  - Lower patience stops training sooner, saving time
- **Behavior**:
  - Counter resets to 0 whenever validation loss improves
  - Training stops when counter reaches patience value
  - Best model weights are automatically loaded after stopping

### `grad_clip` (float)
- **Description**: Maximum gradient norm for gradient clipping
- **Default**: `1.0`
- **Typical Range**: `0.5` to `5.0`
- **Recommended**:
  - Aggressive clipping: `0.5` to `1.0`
  - Moderate clipping: `1.0` to `2.0`
  - Light clipping: `3.0` to `5.0`
- **Impact**:
  - **Critical for LSTM training** - prevents exploding gradients
  - Limits the magnitude of gradient updates
  - Too aggressive clipping can slow convergence
- **Notes**: Applied using `torch.nn.utils.clip_grad_norm_` after loss.backward()

---

## Learning Rate Scheduler Parameters

The training uses **ReduceLROnPlateau** scheduler (automatic, not user-configurable):

- **Mode**: `min` (monitors decreasing validation loss)
- **Factor**: `0.5` (reduces LR by 50% when triggered)
- **Patience**: `5` epochs (waits 5 epochs of no improvement before reducing)
- **Verbose**: `True` (logs LR reductions)

**Behavior Example**:
```
Epoch 1-10: LR = 0.001
Epoch 11-15: Val loss stops improving
Epoch 16: LR reduced to 0.0005
Epoch 16-25: Training with lower LR
Epoch 26: LR reduced to 0.00025 (if still not improving)
```

---

## Data Processing Notes

### Sequence Length
- **Fixed**: `10` time steps (hardcoded in `TimeSeriesLSTM.__init__`)
- **Meaning**: Model looks at 10 consecutive days to predict the next day
- **To Change**: Modify `seq_len` parameter in dataset initialization
- **Recommendation**: Consider making this configurable (5-60 days typical)

### Feature Scaling
- **Method**: MinMaxScaler (scales to [0, 1] range)
- **Fit**: Only on training data
- **Transform**: Same scaler applied to validation data (prevents data leakage)
- **Saved**: Scaler stored as `TimeSeriesLSTM_{ticker}_scaler.pkl`
- **Critical**: Validation dataset MUST reuse training scaler

### Data Loading
- **Order**: Time series order is strictly preserved (no shuffling)
- **Workers**: 2 parallel data loading workers
- **Pin Memory**: Enabled if GPU available (faster data transfer)

---

## GPU/Hardware Parameters

### Device Selection (Automatic)
- **Detection**: Automatically uses GPU if available via `torch.cuda.is_available()`
- **Fallback**: Uses CPU if no GPU detected
- **Logged**: Device selection logged at training start

### Memory Optimization
- **Pin Memory**: Enabled for GPU training (speeds up CPU→GPU transfer)
- **Num Workers**: 2 (parallel data loading)
- **Batch Size**: Adjust if running out of GPU memory

---

## Output Artifacts

### Model Files
- **Best Model**: `{mdl_dir}/TimeSeriesLSTM_{ticker}_best.pth`
  - Saved whenever validation loss improves
  - Final model loaded from best checkpoint
- **Final Model**: `{mdl_dir}/TimeSeriesLSTM_{ticker}.pth`
  - Identical to best model (loaded after training completes)

### Scaler File
- **Location**: `{obj_dir}/TimeSeriesLSTM_{ticker}_scaler.pkl`
- **Format**: Joblib pickle file
- **Contents**: Fitted MinMaxScaler object
- **Usage**: Required for prediction (must use same scaler)

### Metrics File
- **Location**: `{obj_dir}/TimeSeriesLSTM_{ticker}_metrics.pkl`
- **Format**: Joblib pickle file
- **Contents**:
  ```python
  {
      'train_losses': [0.045, 0.038, ...],      # Loss per epoch
      'val_losses': [0.052, 0.047, ...],        # Validation loss per epoch
      'learning_rates': [0.001, 0.001, ...],    # LR per epoch
      'best_epoch': 18,                          # Epoch with best val loss
      'best_val_loss': 0.014532,                # Best validation loss achieved
      'final_train_loss': 0.012345,             # Training loss at end
      'final_val_loss': 0.015678                # Validation loss at end
  }
  ```

---

## Example Configurations

### Minimal Configuration (Use Defaults)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume"]
}
```

### Standard Configuration (Recommended)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume", "sma_value", "sma_value"],
  "epochs": 100,
  "hidden_size": 128,
  "num_layers": 2,
  "dropout": 0.3,
  "batch_size": 64,
  "learning_rate": 0.001,
  "patience": 15
}
```

### High-Capacity Model (Large Dataset)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume", "sma_value", "sma_value", "sma_value"],
  "epochs": 200,
  "hidden_size": 256,
  "num_layers": 3,
  "dropout": 0.3,
  "batch_size": 128,
  "learning_rate": 0.001,
  "weight_decay": 1e-5,
  "patience": 20,
  "train_split": 0.85
}
```

### Conservative Training (Prevent Overfitting)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume"],
  "epochs": 150,
  "hidden_size": 64,
  "num_layers": 2,
  "dropout": 0.4,
  "batch_size": 32,
  "learning_rate": 0.0005,
  "weight_decay": 1e-4,
  "patience": 10,
  "train_split": 0.75
}
```

### Fast Experimentation
```json
{
  "ticker": "AAPL",
  "f_cols": ["close", "volume"],
  "epochs": 50,
  "hidden_size": 32,
  "num_layers": 1,
  "dropout": 0.2,
  "batch_size": 32,
  "patience": 8
}
```

---

## Training Log Example

```
Training on device: cuda
Train size: 1200, Validation size: 300
Starting training for 100 epochs...
Epoch 1/100 - Train Loss: 0.045231, Val Loss: 0.052341, LR: 0.001000
New best model saved! Val Loss: 0.052341
Epoch 2/100 - Train Loss: 0.038456, Val Loss: 0.047892, LR: 0.001000
New best model saved! Val Loss: 0.047892
...
Epoch 18/100 - Train Loss: 0.012456, Val Loss: 0.014532, LR: 0.001000
New best model saved! Val Loss: 0.014532
...
Epoch 25/100 - Train Loss: 0.010234, Val Loss: 0.015123, LR: 0.000500
(no improvement for 7 epochs, LR reduced)
...
Epoch 33/100 - Train Loss: 0.009876, Val Loss: 0.015456, LR: 0.000500
Early stopping triggered at epoch 33. Best epoch was 18
Training complete! Best Val Loss: 0.014532 at epoch 18
```

---

## Troubleshooting

### Problem: Training Loss Decreases but Validation Loss Increases
- **Cause**: Overfitting
- **Solutions**:
  - Increase `dropout` (try 0.3-0.5)
  - Increase `weight_decay` (try 1e-4)
  - Reduce `hidden_size` or `num_layers`
  - Reduce `train_split` to get more validation data

### Problem: Both Losses Remain High
- **Cause**: Underfitting or insufficient capacity
- **Solutions**:
  - Increase `hidden_size` (try 128-256)
  - Increase `num_layers` (try 3-4)
  - Decrease `dropout`
  - Increase `epochs` or `patience`
  - Add more features to `f_cols`

### Problem: Training is Very Slow
- **Cause**: Large model or CPU training
- **Solutions**:
  - Reduce `batch_size` if GPU memory limited
  - Reduce `hidden_size` or `num_layers`
  - Use GPU if available
  - Reduce `epochs`
  - Reduce number of features

### Problem: "Exploding Gradients" or NaN Loss
- **Cause**: Gradient instability
- **Solutions**:
  - Decrease `learning_rate` (try 0.0005 or 0.0001)
  - Decrease `grad_clip` (try 0.5)
  - Reduce model complexity
  - Check for data quality issues (NaN values, extreme outliers)

### Problem: Early Stopping Too Soon
- **Cause**: Not enough patience or noisy validation metrics
- **Solutions**:
  - Increase `patience` (try 20-30)
  - Increase `train_split` (more training data)
  - Increase `batch_size` (more stable gradients)

### Problem: GPU Out of Memory
- **Cause**: Model or batch size too large
- **Solutions**:
  - Reduce `batch_size` (try 32 or 16)
  - Reduce `hidden_size`
  - Reduce `num_layers`
  - Use gradient accumulation (requires code changes)

---

## Performance Benchmarks

Typical training times on different hardware (100 epochs, 1000 samples):

| Hardware | Hidden Size | Batch Size | Time per Epoch | Total Time |
|----------|-------------|------------|----------------|------------|
| CPU (M1) | 64 | 32 | ~2-3 sec | ~5 min |
| CPU (M1) | 128 | 64 | ~4-5 sec | ~8 min |
| GPU (RTX 3080) | 128 | 64 | ~0.5 sec | ~1 min |
| GPU (RTX 3080) | 256 | 128 | ~1 sec | ~2 min |

*Note: Actual times vary based on number of features, sequence length, and early stopping*

---

## Best Practices

1. **Start Simple**: Begin with default parameters and small models
2. **Monitor Both Losses**: Watch train vs validation loss to detect overfitting
3. **Use Early Stopping**: Don't disable it - saves time and prevents overfitting
4. **Save Metrics**: Always save and review training metrics
5. **Iterate**: Adjust parameters based on loss curves and validation performance
6. **GPU Usage**: Use GPU for models with hidden_size > 128 or large datasets
7. **Feature Selection**: More features ≠ better; remove low-correlation features
8. **Sequence Length**: Consider making this configurable for your use case
9. **Validation Size**: Ensure validation set has enough samples (100+ recommended)
10. **Reproducibility**: Set random seeds for reproducible results (not currently implemented)

---

## Future Improvements

Parameters that could be added in the future:

- `seq_len`: Configurable sequence length (currently fixed at 10)
- `target_col`: Predict single target instead of all features
- `loss_function`: Choose between MSE, MAE, Huber loss
- `optimizer`: Choose between Adam, AdamW, SGD
- `scheduler_type`: Different LR scheduling strategies
- `bidirectional`: Enable bidirectional LSTM
- `attention`: Add attention mechanism
- `validation_split_method`: Walk-forward vs fixed split
- `random_seed`: For reproducibility
- `checkpoint_frequency`: Save checkpoints every N epochs
- `tensorboard`: Enable TensorBoard logging

---

## Version History

- **2026-02-06**: Initial documentation with all quick win improvements
  - Added train/val split
  - Added gradient clipping
  - Added learning rate scheduler
  - Added early stopping
  - Added dropout regularization
  - Added GPU support
  - Added comprehensive metrics tracking
