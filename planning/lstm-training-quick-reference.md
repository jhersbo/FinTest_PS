# LSTM Training Parameters - Quick Reference

**Last Updated**: 2026-02-06
**Full Documentation**: [lstm-training-parameters.md](./lstm-training-parameters.md)

---

## Parameter Quick Lookup

| Parameter | Type | Default | Range | Impact |
|-----------|------|---------|-------|--------|
| **ticker** | string | - | - | **Required** - Stock symbol |
| **f_cols** | list[string] | - | - | **Required** - Feature columns |
| **epochs** | int | 100 | 50-500 | Max training iterations |
| **hidden_size** | int | 64 | 32-512 | Model capacity |
| **num_layers** | int | 2 | 1-4 | Model depth |
| **dropout** | float | 0.2 | 0.0-0.5 | Regularization strength |
| **batch_size** | int | 64 | 16-256 | Memory vs stability |
| **learning_rate** | float | 0.001 | 0.0001-0.01 | Training speed |
| **weight_decay** | float | 1e-5 | 0-1e-3 | L2 regularization |
| **patience** | int | 15 | 5-30 | Early stopping wait |
| **grad_clip** | float | 1.0 | 0.5-5.0 | Gradient stability |
| **train_split** | float | 0.8 | 0.7-0.9 | Train/val ratio |

---

## Common Configurations

### 🚀 Quick Start (Use Defaults)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume"]
}
```

### ⭐ Recommended (Balanced)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume", "sma_value"],
  "hidden_size": 128,
  "num_layers": 2,
  "dropout": 0.3,
  "epochs": 100,
  "patience": 15
}
```

### 🔬 Experimentation (Fast)
```json
{
  "ticker": "AAPL",
  "f_cols": ["close", "volume"],
  "hidden_size": 32,
  "num_layers": 1,
  "epochs": 50,
  "patience": 8
}
```

### 💪 High Capacity (Large Dataset)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close", "volume", "sma_value", "sma_value"],
  "hidden_size": 256,
  "num_layers": 3,
  "dropout": 0.3,
  "batch_size": 128,
  "epochs": 200,
  "patience": 20
}
```

### 🛡️ Anti-Overfitting (Conservative)
```json
{
  "ticker": "AAPL",
  "f_cols": ["open", "high", "low", "close"],
  "hidden_size": 64,
  "dropout": 0.4,
  "weight_decay": 1e-4,
  "learning_rate": 0.0005,
  "train_split": 0.75,
  "patience": 10
}
```

---

## Troubleshooting Cheat Sheet

| Problem | Solution |
|---------|----------|
| 📈 Train ↓ but Val ↑ (Overfitting) | ⬆️ `dropout`, ⬆️ `weight_decay`, ⬇️ `hidden_size` |
| 📊 Both losses high (Underfitting) | ⬆️ `hidden_size`, ⬆️ `num_layers`, ⬇️ `dropout` |
| 🐌 Training too slow | ⬇️ `batch_size`, ⬇️ `hidden_size`, use GPU |
| 💥 NaN/exploding gradients | ⬇️ `learning_rate`, ⬇️ `grad_clip` to 0.5 |
| ⏹️ Stops too early | ⬆️ `patience`, ⬆️ `train_split` |
| 💾 GPU out of memory | ⬇️ `batch_size`, ⬇️ `hidden_size` |

---

## What Gets Saved

```
artifacts/
├── model_output/
│   ├── TimeSeriesLSTM_{ticker}.pth          # Final model
│   └── TimeSeriesLSTM_{ticker}_best.pth     # Best checkpoint
└── objects/
    ├── TimeSeriesLSTM_{ticker}_scaler.pkl   # Feature scaler
    └── TimeSeriesLSTM_{ticker}_metrics.pkl  # Training history
```

---

## Training Metrics Structure

```python
{
    'train_losses': [0.045, 0.038, ...],     # Per epoch
    'val_losses': [0.052, 0.047, ...],       # Per epoch
    'learning_rates': [0.001, 0.001, ...],   # Per epoch
    'best_epoch': 18,
    'best_val_loss': 0.014532,
    'final_train_loss': 0.012345,
    'final_val_loss': 0.015678
}
```

---

## Available Features

- `open` - Opening price
- `high` - High price
- `low` - Low price
- `close` - Closing price
- `volume` - Trading volume
- `sma_value` - 20-day SMA
- `sma_value` - 50-day SMA
- `sma_value` - 200-day SMA

---

## Auto-Applied Features

✅ **Enabled by Default (not configurable)**:
- Train/validation split (temporal order)
- Gradient clipping
- Learning rate scheduler (ReduceLROnPlateau)
- Early stopping with best model restore
- GPU auto-detection
- MinMaxScaler normalization
- Metrics tracking

---

## Load Metrics (Python)
```python
import joblib
metrics = joblib.load("artifacts/objects/TimeSeriesLSTM_AAPL_metrics.pkl")
print(f"Best val loss: {metrics['best_val_loss']}")
```

---

## Performance Tips

1. **Small dataset (< 500)**: `hidden_size=32-64`, `dropout=0.3-0.4`
2. **Medium dataset (500-5000)**: `hidden_size=64-128`, `dropout=0.2-0.3`
3. **Large dataset (> 5000)**: `hidden_size=128-256`, `dropout=0.2`
4. **Always monitor** both train and val losses
5. **Use GPU** for hidden_size > 128
6. **Start simple**, then increase complexity

---

## Dataset Size Recommendations

| Dataset Size | hidden_size | num_layers | batch_size | dropout |
|--------------|-------------|------------|------------|---------|
| < 500 | 32-64 | 1-2 | 16-32 | 0.3-0.4 |
| 500-2000 | 64-128 | 2 | 32-64 | 0.2-0.3 |
| 2000-5000 | 128-256 | 2-3 | 64-128 | 0.2-0.3 |
| > 5000 | 256-512 | 3-4 | 128-256 | 0.2 |

---

## Training Time Estimates

**100 epochs, 1000 samples**:

| Hardware | Config | Time |
|----------|--------|------|
| CPU (M1) | hidden=64, batch=32 | ~5 min |
| CPU (M1) | hidden=128, batch=64 | ~8 min |
| GPU (RTX 3080) | hidden=128, batch=64 | ~1 min |
| GPU (RTX 3080) | hidden=256, batch=128 | ~2 min |

*Early stopping typically reduces actual training by 30-50%*

---

## Learning Rate Scheduler Behavior

```
Start: LR = 0.001
↓ (5 epochs no improvement)
LR = 0.0005 (×0.5)
↓ (5 epochs no improvement)
LR = 0.00025 (×0.5)
↓ (15 epochs no improvement)
Early stopping triggered
```

---

## Quick Decision Tree

```
Is dataset < 500 samples?
├─ YES → hidden_size=32-64, dropout=0.4, train_split=0.7
└─ NO → Continue

Is overfitting (val_loss >> train_loss)?
├─ YES → Increase dropout/weight_decay, decrease hidden_size
└─ NO → Continue

Is underfitting (both losses high)?
├─ YES → Increase hidden_size/num_layers, add features
└─ NO → Continue

Training too slow?
├─ YES → Decrease model size, reduce epochs, use GPU
└─ NO → You're good! 🎉
```

---

For detailed explanations, see [lstm-training-parameters.md](./lstm-training-parameters.md)
