# CLAUDE.md

## Project Overview

**FinTest Prediction Service** is a stock market prediction platform that uses deep learning (LSTM neural networks) to forecast time series data for financial assets. The system manages the complete ML lifecycle from data ingestion to model training and prediction, with a focus on asynchronous job processing and scalable architecture.

**Core Capabilities**:
- Time series LSTM model training with advanced regularization
- Asynchronous batch job processing for long-running ML tasks
- Stock ticker data management and timeseries analysis
- Model versioning and artifact management
- Training run tracking and metrics persistence

## Tech Stack

**Backend & API**:
- **FastAPI** - Modern async web framework for REST API
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and settings management

**Machine Learning**:
- **PyTorch** - Deep learning framework for LSTM models
- **scikit-learn** - Data preprocessing (MinMaxScaler)
- **joblib** - Model and metrics serialization

**Data & Database**:
- **PostgreSQL** - Primary database (via SQLAlchemy)
- **SQLAlchemy** - Async ORM with custom base models
- **pandas** - Data manipulation for timeseries

**Job Queue & Processing**:
- **Redis** - Message broker and cache
- **RQ (Redis Queue)** - Distributed job queue for async training

**Development**:
- **Python 3.11+** - Type hints and modern Python features

## Architecture

### Directory Structure
```
FinTest_PS/
├── app/
│   ├── api/           # FastAPI routes and endpoints
│   ├── batch/         # Job queue system (RQ workers)
│   │   ├── job.py     # Base Job class
│   │   └── models/    # JobUnit, JobQueue models
│   ├── core/          # Core utilities (config, logging, DB)
│   ├── ml/
│   │   ├── core/      # ML base models (ModelType, TrainingRun)
│   │   ├── data/      # Data models (Ticker, TickerTimeseries)
│   │   ├── model_defs/# Neural network definitions (lstm.py)
│   │   └── training/  # Training logic (Trainable, ts_lstm.py)
│   └── main.py        # FastAPI application entry
├── artifacts/
│   ├── model_output/  # Saved PyTorch models (.pth)
│   └── objects/       # Scalers and metrics (.pkl)
├── planning/          # Documentation and parameter guides
└── scripts/           # Worker startup and management
```

### Key Patterns

**1. Job-Based Architecture**
- All long-running tasks (training, data processing) run as async jobs via RQ
- `Job` base class → `Trainable` → specific trainers (e.g., `ts_lstm.Trainer`)
- Jobs tracked via `JobUnit` with status, logs, and metadata

**2. Model Lifecycle**
- `ModelType` defines model architectures (registered in DB)
- `TrainingRun` tracks each training execution with config and metrics
- Models saved as `.pth` files, scalers/metrics as `.pkl`

**3. Database Layer**
- Custom `BaseModel` with SQLAlchemy for CRUD operations
- Async queries with `await Model.find_by_gid()` pattern
- Views for complex queries (e.g., `vw_ticker_timeseries`)

**4. Training Pipeline** (see [planning/lstm-training-quick-reference.md](planning/lstm-training-quick-reference.md))
- Train/validation split (temporal, no shuffling)
- Gradient clipping, learning rate scheduling, early stopping
- Metrics tracking: train/val losses, learning rates, best epoch
- GPU auto-detection with CPU fallback

### Data Flow
```
API Request → JobQueue → RQ Worker → Trainer.run()
                                          ↓
                                     create_run() (TrainingRun)
                                          ↓
                                     TimeSeriesLSTM.train()
                                          ↓
                        [Load Data → Train/Val Split → Training Loop]
                                          ↓
                          Save: model.pth, scaler.pkl, metrics.pkl
```

## Code Style

**Python Conventions**:
- Type hints required for function signatures: `def train(config: dict[str, Any]) -> LSTMModel`
- Async/await for asynchronous database operations: `await Ticker.findByTicker(ticker)`
- Modern list/dict syntax: `list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]`
- Logging via `app.core.utils.logger.get_logger(__name__)`

**General Conventions**:
- Double-quotes take priority

**Class Patterns**:
- PascalCase for classes: `TimeSeriesLSTM`, `JobUnit`
- snake_case for methods/functions: `create_run()`, `get_class_name()`
- Class constants in UPPER_SNAKE_CASE: `NAME = "TimeSeriesLSTM"`

**ML Training Conventions**:
- Always use `shuffle=False` for time series DataLoaders
- Device placement: `model.to(device)`, `tensor.to(device)`
- Save best model during training, load at end
- Track metrics in dict, save with joblib

**Database Models**:
- Inherit from `BaseModel` (app/core/models/base_model.py)
- Use `gid` (UUID) as primary key, not `id`
- Async class methods for queries: `@classmethod async def find_by_gid()`

**Configuration**:
- Centralized config via `app.core.config.config.get_config()`
- Artifact paths: `get_config().mdl_dir`, `get_config().obj_dir`

**Error Handling**:
- Catch specific exceptions: `RuntimeError`, `ValueError`, `torch.cuda.OutOfMemoryError`
- Log with context: `L.error(f"Training failed: {str(e)}", exc_info=True)`
- Update job status in finally blocks

**Documentation**:
- Comprehensive parameter docs in [planning/](planning/)
- Quick reference guides for user-facing features
- Code comments for non-obvious logic (e.g., dropout behavior, gradient clipping)