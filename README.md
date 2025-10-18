# FinTest PS API

## Starting the application:

### Docker (Recommended)
```bash
docker compose up --build
```

### Locally (API layer only)
```bash
uvicorn app.api.main:app --reload
```