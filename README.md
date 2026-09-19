# AI College Notification Hub

A production-ready college notification management and AI analysis platform.

## Architecture

This repository contains the backend service:
- **Backend**: Built with Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic v2, and OpenAI-compatible AI API. See [`backend/README.md`](file:///backend/README.md) for full setup instructions and API contract.

## Quick Start (Backend)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)