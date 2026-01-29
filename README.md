# Fair Exchange Dice

A fair exchange dice application with a Django REST API server and FastAPI client.

## Services

| Service | Port | Description |
|---------|------|-------------|
| db | 5432 | PostgreSQL 16 database |
| server | 8000 | Django REST API |
| client | 8001 | FastAPI client |

## Quick Start (Docker)

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Hot Reload (Development)

Changes to your code are automatically reloaded. Both Django and FastAPI watch for file changes.

For enhanced file sync, use Docker Compose watch mode:

```bash
docker compose watch
```

## Access

- Django API: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- FastAPI Client: http://localhost:8001
- FastAPI Docs: http://localhost:8001/docs

## Local Development (without Docker)

### Requirements

- Python 3.12+
- PostgreSQL

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

### Run Django Server

```bash
cd server
python manage.py migrate
python manage.py runserver
```

### Run FastAPI Client

```bash
cd client
uvicorn main:app --reload --port 8001
```
