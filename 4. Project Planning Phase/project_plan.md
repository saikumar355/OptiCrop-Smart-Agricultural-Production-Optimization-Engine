# Project Planning — OptiCrop AI

## Development Phases

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Project scaffold, config, utils, extensions | ✅ Complete |
| 2 | ML pipeline (ingestion, preprocessing, training, evaluation, selection) | ✅ Complete |
| 3 | Prediction Engine | ✅ Complete |
| 4 | Flask application factory | ✅ Complete |
| 5 | Data layer (SQLite repository) | ✅ Complete |
| 6 | Service layer (recommendation, suitability, admin, dashboard, analytics) | ✅ Complete |
| 7 | Controllers | ✅ Complete |
| 8 | Routes and Blueprints | ✅ Complete |
| 9 | Frontend (templates, CSS, JS) | ✅ Complete |
| 10 | Security hardening (CSRF, rate limiting, IP hashing) | ✅ Complete |
| 11 | Test suite (unit + property-based) | ✅ Complete |
| 12 | Deployment config (Docker, Gunicorn) | ✅ Complete |

## Technology Choices

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | ML ecosystem, Flask, ease of deployment |
| ML Framework | scikit-learn + XGBoost | Industry standard, 9 algorithms |
| Web Framework | Flask 3.0 | Lightweight, Python-native |
| Database | SQLite | Zero-config, sufficient for v1 |
| Frontend | Bootstrap 5 + Vanilla JS | No build step, responsive, accessible |
| Testing | pytest + Hypothesis | Unit + property-based correctness |
| Container | Docker + Gunicorn | Production-grade deployment |

## Team Roles (suggested)

| Role | Responsibilities |
|---|---|
| ML Engineer | Pipeline, model training, evaluation |
| Backend Engineer | Flask app, services, repositories, security |
| Frontend Engineer | Templates, CSS, JavaScript modules |
| DevOps | Docker, deployment, environment config |
| QA | Test suite, property-based tests |
