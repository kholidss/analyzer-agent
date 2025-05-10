FROM python:3.11-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create app dir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential poppler-utils

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app/ ./app
COPY .env .

# Set FastAPI start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]