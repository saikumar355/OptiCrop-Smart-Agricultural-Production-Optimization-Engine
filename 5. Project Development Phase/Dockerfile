# -------- Stage 1: Builder --------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --prefix=/install --no-cache-dir -r requirements.txt

# -------- Stage 2: Runtime --------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user for security
RUN groupadd -r opticrop && useradd -r -g opticrop opticrop

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=opticrop:opticrop . .

# Create persistent directories
RUN mkdir -p logs saved_models instance datasets app/static/eda && \
    chown -R opticrop:opticrop logs saved_models instance datasets app/static/eda

USER opticrop

ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
