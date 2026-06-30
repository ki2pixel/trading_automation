FROM python:3.11-slim

# Avoid writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Force stdout/stderr streams to be unbuffered
ENV PYTHONUNBUFFERED=1
# Set PYTHONPATH so backtest_engine can be imported correctly
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (e.g. curl for health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first to leverage caching
COPY requirements-backtest-engine.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-backtest-engine.txt

# Copy source directories and the runner
COPY backtest_engine/ /app/backtest_engine/
COPY configs/ /app/configs/
COPY pine_scripts_convert_to_python/ /app/pine_scripts_convert_to_python/
COPY run_ingestor.py .
COPY run_paper_trader.py .

# Create cache directory
RUN mkdir -p /app/cache

# Default environment variables
ENV T212_PRICE_CACHE_PATH=/app/cache/t212_prices.json
ENV PORT=8080
ENV T212_INGESTOR_MODE=worker
ENV T212_BOOTSTRAP=false
ENV T212_POLLING_INTERVAL=60

EXPOSE 8080

# Run the entrypoint script
CMD ["python", "run_ingestor.py"]
