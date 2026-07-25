FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and datasets
COPY backend/ /app/
COPY datasets/ /datasets/

ENV PORT=9000
ENV DATASETS_DIR=/datasets
ENV DUCKDB_PATH=crime_stats.duckdb

EXPOSE 9000

# Run start.sh script which builds DuckDB and starts Uvicorn
RUN chmod +x /app/start.sh
CMD ["./start.sh"]
