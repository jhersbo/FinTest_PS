# FinTest Prediction Service

Stock market prediction platform powered by machine learning. Manages the full ML lifecycle: data ingestion, async model training, and prediction serving.

## Stack

- **API**: FastAPI + Uvicorn
- **ML**: PyTorch, scikit-learn
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Job Queue**: Redis + RQ for async training jobs

## Project Structure

```
app/
├── api/       # REST API routes and middleware
├── batch/     # Async job queue system (RQ workers)
├── core/      # Config, logging, database utilities
└── ml/        # Models, training logic, data management
artifacts/     # Saved models and serialized objects
```

## Getting Started

### Docker (Recommended)
```bash
docker compose up --build
```

### Locally (API only)
```bash
uvicorn app.api.main:app --reload
```
Requires external PostgreSQL and Redis instances.