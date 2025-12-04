# Use official Python image
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install system deps for Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Run FastAPI using uvicorn
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
