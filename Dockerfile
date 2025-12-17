FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY cloudflare_saas/ ./cloudflare_saas/
COPY examples/ ./examples/
COPY setup.py .
COPY README.md .

# Install package
RUN pip install -e .

# Expose port
EXPOSE 8000

# Run FastAPI application
CMD ["uvicorn", "examples.fastapi_integration:app", "--host", "0.0.0.0", "--port", "8000"]