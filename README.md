# OptiCrop

OptiCrop is a production-grade agricultural AI platform that recommends the optimal crop to cultivate based on soil chemistry and environmental inputs. It uses an ensemble ML model (Extra Trees, F1-weighted = 0.93) trained on a labeled agronomic dataset. The platform exposes a Flask REST API, a multi-page frontend, and an admin dashboard — all deployable via Docker.

---

## Features

- ML-based crop recommendation with confidence scores
- Threshold-based suitability analysis across all supported crops
- Paginated prediction history with SHA-256 IP hashing (no raw IPs stored)
- Admin dashboard: active model metadata, background retraining, system health
- Analytics and dashboard views with Chart.js visualizations
- CSRF protection, per-IP rate limiting, structured logging

---

## Prerequisites

- Python 3.12+
- pip
- Docker and Docker Compose (optional, for containerised deployment)

---

## Quick Start — Local

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file and fill in values:
   ```bash
   cp .env.example .env
   # Edit .env — set SECRET_KEY, CSRF_SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, etc.
   ```

3. Train the model:
   ```bash
   python scripts/train.py
   ```
   This writes `saved_models/<ModelName>_<timestamp>.pkl`, `saved_models/scaler_<timestamp>.pkl`, and `saved_models/metadata.json`.

4. Update `ACTIVE_MODEL_PATH` and `ACTIVE_SCALER_PATH` in `.env` with the exact filenames generated in step 3.

5. Start the application:
   ```bash
   python wsgi.py
   # or
   python -m flask run
   ```

The app is available at `http://localhost:5000`.

---

## Quick Start — Docker

```bash
docker-compose up --build
```

Docker Compose starts the app on port 5000, mounts named volumes for the database, models, logs, datasets, and EDA images, and runs a health check against `/api/health`.

---

## Documentation

| Document | Description |
|---|---|
| [docs/installation.md](docs/installation.md) | Full step-by-step installation guide |
| [docs/architecture.md](docs/architecture.md) | System architecture, layers, and data flow |
| [docs/api.md](docs/api.md) | REST API reference for all endpoints |
| [docs/deployment.md](docs/deployment.md) | Production deployment guide (Gunicorn, Nginx, logrotate) |
| [docs/docker.md](docs/docker.md) | Docker and Docker Compose usage guide |

---

## Project Structure

```
opticrop/
├── app/               # Flask application (routes, controllers, services, etc.)
├── ml/                # Standalone ML pipeline modules
├── scripts/train.py   # ML pipeline entry point
├── datasets/          # Training CSV
├── saved_models/      # Serialized model and scaler artifacts
├── docs/              # Documentation
├── tests/             # Pytest unit, integration, and property-based tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## License

This project is for educational and agricultural research purposes.
