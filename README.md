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
- Django Swagger: http://localhost:8000/api/docs/
- Django ReDoc: http://localhost:8000/api/redoc/
- Django OpenAPI Schema: http://localhost:8000/api/schema/
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

## Testing

### Run All Tests

```bash
# Django (server)
cd server && python manage.py test

# FastAPI (client)
cd client && pytest
```

### Django Tests

```bash
# Run all tests
python manage.py test

# Verbose output
python manage.py test -v 2

# Run specific app tests
python manage.py test authentication
```

### FastAPI Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific test file
pytest test_main.py
```

## Coverage

### Django Coverage

```bash
cd server
coverage run manage.py test
coverage html
# Open server/htmlcov/index.html
```

### FastAPI Coverage

```bash
cd client
coverage run -m pytest
coverage html
# Open client/htmlcov/index.html
```

### View Coverage Report

Open `htmlcov/index.html` in your browser to see:
- Overall coverage percentage
- Per-file coverage breakdown
- Line-by-line highlighting (green = covered, red = not covered)

**Coverage targets:**
- Aim for 80%+ coverage on new code
- Red lines in the report indicate untested code paths
