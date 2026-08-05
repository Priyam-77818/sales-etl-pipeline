# ── Base image ────────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/cleaned data/transformed logs

# Default command — runs the full pipeline end-to-end
CMD ["python", "run_pipeline.py"]
