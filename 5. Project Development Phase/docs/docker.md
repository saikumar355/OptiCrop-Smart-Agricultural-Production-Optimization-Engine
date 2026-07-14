# Docker Guide

This guide covers building and running OptiCrop with Docker and Docker Compose.

---

## Prerequisites

- Docker 24+
- Docker Compose v2 (`docker compose` command)

---

## Quick Start

```bash
# 1. Copy and fill in environment variables
cp .env.example .env

# 2. Build and start the container
docker compose up --build

# 3. Open in browser
open http://localhost:5000
```

The container exposes port 5000. Named volumes persist the database, model artifacts, logs, dataset, and EDA images across restarts.

---

## Environment Variables

Before starting the container, ensure your `.env` file (or shell environment) sets **all required variables**:

```ini
SECRET_KEY=<long_random_string>
CSRF_SECRET_KEY=<long_random_string>
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt_hash>
ACTIVE_MODEL_PATH=saved_models/ExtraTrees_<timestamp>.pkl
ACTIVE_SCALER_PATH=saved_models/scaler_<timestamp>.pkl
SUITABILITY_THRESHOLDS={}
```

See `.env.example` for the full list. The app halts on startup if any required variable is absent.

---

## Running the Training Pipeline Inside Docker

The training script is included in the image. Run it as a one-off container to produce model artifacts:

```bash
docker compose run --rm opticrop python scripts/train.py
```

This writes artifacts into the `opticrop_models` named volume. After training, update `ACTIVE_MODEL_PATH` and `ACTIVE_SCALER_PATH` to the generated filenames, then restart the app container:

```bash
docker compose restart opticrop
```

---

## Named Volumes

| Volume | Mount path | Contents |
|---|---|---|
| `opticrop_db` | `/app/instance` | SQLite database |
| `opticrop_models` | `/app/saved_models` | `.pkl` artifacts + `metadata.json` |
| `opticrop_logs` | `/app/logs` | Application log files |
| `opticrop_datasets` | `/app/datasets` | Training CSV |
| `opticrop_eda` | `/app/app/static/eda` | EDA PNG plots |

To inspect a volume:

```bash
docker volume inspect opticrop_opticrop_models
```

To back up the database:

```bash
docker run --rm \
  -v opticrop_opticrop_db:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/opticrop_db_backup.tar.gz /data
```

---

## Multi-Worker Rate Limiting

The default `RATELIMIT_STORAGE_URL=memory://` uses each Gunicorn worker's own in-process store. With 4 workers a client can exceed the configured limit by up to 4×. For production deployments with multiple workers, use Redis:

1. Add a Redis service to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

2. Set the environment variable:

```ini
RATELIMIT_STORAGE_URL=redis://redis:6379
```

---

## Health Check

The container runs a health check every 30 seconds against `/api/health`:

```bash
curl http://localhost:5000/api/health
# {"status": "ok", "uptime_seconds": 42}
```

Check container health status:

```bash
docker inspect --format='{{.State.Health.Status}}' opticrop_app
```

---

## Useful Commands

```bash
# View live logs
docker compose logs -f opticrop

# Open a shell in the running container
docker compose exec opticrop bash

# Stop and remove containers (volumes are preserved)
docker compose down

# Stop, remove containers AND volumes (destructive)
docker compose down -v

# Rebuild after code changes
docker compose up --build --force-recreate
```

---

## Image Details

- Base image: `python:3.12-slim`
- Multi-stage build: builder stage installs dependencies; runtime stage copies only the installed packages
- Non-root user: `opticrop` (UID/GID via `groupadd` / `useradd`)
- WSGI server: Gunicorn with `gunicorn.conf.py`
- Health check: HTTP probe to `/api/health` every 30s
