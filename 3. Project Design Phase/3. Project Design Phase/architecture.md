# Architecture

OptiCrop is split into two decoupled subsystems:

1. **Offline ML pipeline** (`scripts/train.py` + `ml/`) — runs once to produce serialized model artifacts.
2. **Flask web application** (`app/`) — loads those artifacts at startup and serves predictions via HTTP.

The two subsystems never import each other. The pipeline writes `.pkl` files; the app reads them.

---

## Clean Architecture Layers

The Flask application enforces strict separation of concerns across five layers:

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `app/routes/` | HTTP request intake, CSRF / rate-limit enforcement, response serialization |
| Controllers | `app/controllers/` | Orchestrate the request lifecycle: validate input, call service, format response |
| Services | `app/services/` | Business logic — recommendation, suitability, admin operations |
| Repositories | `app/repositories/` | All SQLite access; no SQL outside this layer |
| Prediction Engine | `app/ml/prediction_engine.py` | Load model artifact; pure `predict()` inference; no Flask or DB imports |

### Layer Import Rules

- Routes **may** import controllers.
- Controllers **may** import services, validators, and config.
- Services **may** import repositories, `PredictionEngine`, and config.
- Repositories **may** import config and `sqlite3` only.
- `PredictionEngine` **may** import `pickle`, `numpy`, `sklearn`, and config only.
- `ml/` pipeline modules **must not** import any `app/` module.
- `app/` modules **must not** import any `ml/` module.

---

## Component Diagram

```
Browser ──► Routes (Blueprints)
               │
               ▼
          Controllers
               │
       ┌───────┴──────────┐
       ▼                  ▼
RecommendationService  SuitabilityService  AdminService  ...
       │                  │
       ▼                  ▼
PredictionEngine     Config (thresholds)
       │
       ▼
 saved_models/*.pkl
       │
  PredictionRepository
       │
  instance/opticrop.db (SQLite)
```

The offline ML pipeline feeds into `saved_models/` independently:

```
datasets/*.csv
   │
Ingestion → Preprocessor → Trainer → Evaluator → ModelSelector
                                                       │
                                               saved_models/
                                          (*.pkl + metadata.json)
```

---

## ML Pipeline

The pipeline is invoked by running `python scripts/train.py`. It executes these steps in order:

1. **Ingestion** (`ml/ingestion.py`) — reads the CSV from the path in config; validates non-empty.
2. **Preprocessor** (`ml/preprocessor.py`) — in order: missing value handling, duplicate removal, outlier treatment, feature scaling (fits scaler), feature engineering, Pearson correlation analysis, class distribution analysis. Writes EDA PNG files to `app/static/eda/`.
3. **Train/test split** — stratified, seeded from config.
4. **Trainer** (`ml/trainer.py`) — trains nine algorithms: Logistic Regression, Decision Tree, Random Forest, KNN, Naive Bayes, SVM, Gradient Boosting, Extra Trees, XGBoost.
5. **Evaluator** (`ml/evaluator.py`) — k-fold cross-validation, hyperparameter tuning (grid or random search), metric computation (accuracy, F1-weighted, precision-weighted, recall-weighted, ROC-AUC).
6. **ModelSelector** (`ml/model_selector.py`) — selects the model with the highest F1-weighted score (tie-break: precision-weighted, then alphabetical). Serializes model + scaler to `saved_models/` with UTC-timestamped filenames. Writes `metadata.json`.

Output artifacts:
```
saved_models/
├── ExtraTrees_2026-07-01T122126Z.pkl   # serialized best model
├── scaler_2026-07-01T122126Z.pkl       # fitted StandardScaler
└── metadata.json                        # model name, F1 score, timestamp
```

After training, update `ACTIVE_MODEL_PATH` and `ACTIVE_SCALER_PATH` in `.env`.

---

## Flask Application Startup

When `create_app()` is called:

1. Config is loaded from environment variables (`DevelopmentConfig` or `ProductionConfig`).
2. Logger is initialised (writes to `logs/opticrop.log`; falls back to stdout if path is inaccessible).
3. CSRF protection (`Flask-WTF`) and rate limiter (`Flask-Limiter`) are attached.
4. `PredictionEngine` is initialised, loading the model and scaler from paths in config. If an artifact is missing, a WARNING is logged and the app continues (non-prediction routes remain available).
5. Blueprints are registered.
6. SQLite database is initialised via `PredictionRepository` (creates the `predictions` table if absent).

---

## Data Flow — Prediction Request

1. `POST /api/recommend` arrives at `recommendation_routes.py`.
2. Flask-Limiter checks the per-IP rate limit. Exceeded → 429.
3. Flask-WTF validates the CSRF token. Invalid → 403.
4. `RecommendationController` calls `InputValidator.validate(data)`:
   - All 7 fields present? Missing → 400 with field names.
   - All values numeric? Non-numeric → 400.
   - All values in range? Out-of-range → 400 with field and range.
5. Controller calls `RecommendationService.recommend(input_vector, hashed_ip)`.
6. Service calls `PredictionEngine.predict(input_vector)`:
   - Scaler transforms the input vector.
   - Model runs inference.
   - Returns `PredictionResult(predicted_label, confidence_score)`.
7. Service calls `PredictionRepository.save(record)` — persists the record to SQLite (stores hashed IP, never raw IP).
8. Controller serializes the result as JSON and returns HTTP 200.
9. On any unhandled exception: global handler logs the full stack trace with a correlation ID and returns `{"error": "internal_error", "correlation_id": "..."}`.

---

## Folder Structure

```
opticrop/
├── app/
│   ├── __init__.py              # Application factory: create_app()
│   ├── config.py                # BaseConfig, DevelopmentConfig, ProductionConfig
│   ├── extensions.py            # Flask-WTF CSRFProtect, Flask-Limiter init
│   ├── controllers/             # Request orchestration
│   ├── routes/                  # Flask Blueprints
│   ├── services/                # Business logic
│   ├── repositories/            # SQLite access (sqlite3, no ORM)
│   ├── ml/
│   │   └── prediction_engine.py # Pure inference class
│   ├── models/                  # Dataclasses: InputVector, PredictionResult, etc.
│   ├── validators/              # Server-side input validation + HTML escaping
│   ├── utils/                   # Logger, hashing, correlation ID
│   ├── static/                  # CSS, JS, EDA PNGs
│   └── templates/               # Jinja2 templates extending base.html
├── ml/                          # Standalone ML pipeline modules
├── scripts/
│   └── train.py                 # Pipeline entry point
├── datasets/                    # Training CSV
├── saved_models/                # Serialized artifacts
├── logs/                        # Application log files
├── instance/                    # SQLite database (opticrop.db)
├── tests/                       # Pytest test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS predictions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT    NOT NULL,   -- UTC ISO 8601
    N                REAL    NOT NULL,
    P                REAL    NOT NULL,
    K                REAL    NOT NULL,
    temperature      REAL    NOT NULL,
    humidity         REAL    NOT NULL,
    rainfall         REAL    NOT NULL,
    ph               REAL    NOT NULL,
    predicted_crop   TEXT    NOT NULL,
    confidence_score REAL    NOT NULL,
    model_name       TEXT    NOT NULL,
    hashed_ip        TEXT    NOT NULL    -- SHA-256 hex digest; raw IP never stored
);

CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
    ON predictions (timestamp DESC);
```

The `PredictionRepository` creates this table on first connection. The database file path is set by `DATABASE_PATH` in config (default: `instance/opticrop.db`).
