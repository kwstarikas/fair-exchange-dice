FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir python-dotenv

# Copy project
COPY . .

# Run migrations and start Django over HTTPS
CMD ["sh", "-c", "python manage.py migrate && uvicorn server.asgi:application --host 0.0.0.0 --port 8000 --ssl-certfile /certs/localhost.pem --ssl-keyfile /certs/localhost-key.pem"]
