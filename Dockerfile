FROM python:3.11-slim AS build
WORKDIR /app
COPY requirements.txt .
# Install dependencies into /app/site-packages
RUN pip install --no-cache-dir --target=/app/site-packages -r requirements.txt
COPY . .

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/site-packages:/app
ENV PATH="/app/site-packages/bin:$PATH"

# Install runtime system dependencies if needed (e.g. libpq for psycopg2)
# python:3.11-slim usually has what's needed for binary wheels, but let's be safe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from build stage
COPY --from=build /app/site-packages /app/site-packages
# Copy application code
COPY . .

# Ensure entrypoint is executable
RUN chmod +x scripts/docker-entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "app.main:app"]
