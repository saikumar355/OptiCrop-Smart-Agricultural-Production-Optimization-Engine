# Implementation Plan: OptiCrop

## Overview

OptiCrop is a production-grade agricultural AI platform. Implementation follows a strict phased order: project scaffold first, then the offline ML pipeline, then the Flask application layers (foundation → data → service → controllers → routes → frontend), then security hardening, then the test suite, and finally deployment configuration and documentation. Each phase builds on the previous; no phase begins until its dependencies are in place.

---

## Tasks

- [ ] 1. Phase 1 — Project Scaffold & Configuration
  - [ ] 1.1 Create the full directory tree and empty `__init__.py` files
    - Create all directories: `app/`, `app/controllers/`, `app/routes/`, `app/services/`, `app/repositories/`, `app/ml/`, `app/models/`, `app/validators/`, `app/utils/`, `app/static/css/`, `app/static/js/`, `app/static/eda/`, `app/templates/admin/`, `app/templates/errors/`, `ml/`, `scripts/`, `tests/property/`, `datasets/`, `saved_models/`, `logs/`, `instance/`, `docs/`
    - Add `__init__.py` to every Python package directory
    - _Requirements: 9.1, 31.1, 31.2_

  - [ ] 1.2 Write `app/config.py` with `BaseConfig`, `DevelopmentConfig`, and `ProductionConfig`
    - Implement the full class hierarchy shown in the design using `os.environ.get()`
    - Include all keys: `SECRET_KEY`, `CSRF_SECRET_KEY`, `DATABASE_PATH`, `MODEL_REGISTRY_PATH`, `ACTIVE_MODEL_PATH`, `ACTIVE_SCALER_PATH`, `DATASET_PATH`, `MISSING_VALUE_STRATEGY`, `OUTLIER_STRATEGY`, `SCALER_TYPE`, `TEST_RATIO`, `RANDOM_SEED`, `CV_FOLDS`, `HYPERPARAM_STRATEGY`, `RECOMMEND_RATE_LIMIT`, `SUITABILITY_RATE_LIMIT`, `RATELIMIT_STORAGE_URL`, `LOG_PATH`, `LOG_LEVEL`, `GUNICORN_WORKERS`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `CHARTJS_URL`, `EDA_STATIC_DIR`, `SUITABILITY_THRESHOLDS`
    - No hardcoded values; all defaults from env
    - _Requirements: 9.4, 16.1, 16.2_

  - [ ] 1.3 Write `app/utils/logger.py` structured logger factory
    - Create `get_logger(name)` returning a logger with file handler (path from `Config.LOG_PATH`) and stream handler fallback if file is inaccessible
    - Include timestamp, severity level, and module name in each log record
    - Ensure raw IP addresses are never written (document in docstring)
    - _Requirements: 17.1, 17.5_

  - [ ] 1.4 Write `app/utils/hashing.py`, `app/utils/correlation_id.py`
    - Implement `sha256_ip(raw_ip: str) -> str` using `hashlib.sha256`
    - Implement `generate_correlation_id() -> str` (8-char hex token)
    - _Requirements: 12.3, 17.2, 17.3_

  - [ ] 1.5 Write `app/extensions.py` — Flask-WTF `CSRFProtect` and Flask-Limiter instances
    - Instantiate `CSRFProtect()` and `Limiter()` without binding to an app (use `init_app` pattern)
    - Source limiter key function from client remote address
    - _Requirements: 14.1, 15.1_

  - [ ] 1.6 Write `requirements.txt` with all pinned dependencies
    - Include: `flask`, `flask-wtf`, `flask-limiter`, `gunicorn`, `scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `hypothesis`, `pytest`, `pytest-cov`, `bcrypt`; all pinned with `==`
    - _Requirements: 29.1, 29.5_

  - [ ] 1.7 Write `.env.example`, `.gitignore`
    - `.env.example`: list all required and optional variables as shown in the design, with no real values
    - `.gitignore`: exclude `.env`, `__pycache__/`, `*.pyc`, `saved_models/*.pkl`, `instance/*.db`, `logs/*.log`, `.pytest_cache/`, `.coverage`
    - _Requirements: 16.4, 16.5_

  - [ ] 1.8 Download and place `datasets/crop_recommendation.csv`
    - Verify the CSV contains the expected columns: `N`, `P`, `K`, `temperature`, `humidity`, `rainfall`, `ph`, `label`
    - Place at `datasets/crop_recommendation.csv` matching the default `DATASET_PATH`
    - _Requirements: 1.1, 1.4_

- [ ] 2. Phase 2 — ML Pipeline
  - [ ] 2.1 Implement `ml/ingestion.py` — CSV ingestion module
    - Read CSV from `Config.DATASET_PATH`; raise `ConfigurationError` with key name if path missing
    - Raise `DataIngestionError` with path if file not found
    - Raise `DataParseError` distinct from `DataIngestionError` on malformed CSV
    - Raise descriptive error if DataFrame has zero rows or zero columns after loading
    - Log row and column counts after successful load
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 2.2 Implement `ml/preprocessor.py` — data preprocessing steps 1–7 in order
    - Step 1: Handle missing values per `Config.MISSING_VALUE_STRATEGY`; log count; raise on invalid strategy
    - Step 2: Remove exact-duplicate rows; log count removed
    - Step 3: Treat outliers per `Config.OUTLIER_STRATEGY` (IQR clip by default); log count treated
    - Step 4: Fit and apply scaler per `Config.SCALER_TYPE` to all 7 numerical features
    - Step 5: Feature engineering (placeholder hook for additional derived features)
    - Step 6: Compute and log Pearson correlation matrix for all numerical features
    - Step 7: Compute and log class distribution (count + relative frequency per class)
    - Return `(preprocessed_df, fitted_scaler)`; no Flask or prediction imports
    - _Requirements: 2.1–2.10_

  - [ ] 2.3 Implement `ml/eda_visualizer.py` — EDA plot generation
    - Generate `correlation_heatmap.png`, `class_distribution.png`, and `feature_hist_<name>.png` for each of the 7 features
    - Save all PNGs to `Config.EDA_STATIC_DIR`
    - _Requirements: 23.2_

  - [ ] 2.4 Implement train/test split logic in `scripts/train.py` (split section only, not the full entry point yet)
    - Apply stratified split with `Config.TEST_RATIO` (validate exclusive range (0,1)) and `Config.RANDOM_SEED`
    - Fall back to non-stratified with warning if any class has < 2 samples
    - Log training set and test set row counts
    - _Requirements: 3.1–3.5_

  - [ ] 2.5 Implement `ml/trainer.py` — multi-algorithm training
    - Instantiate and train all 9 algorithms: Logistic Regression, Decision Tree, Random Forest, KNN, Naive Bayes, SVM, Gradient Boosting, Extra Trees, XGBoost
    - Log algorithm name and start/completion timestamps for each
    - On individual algorithm failure: log error with name and reason, skip, continue
    - Halt with error if training set is empty
    - No preprocessing or Flask imports
    - _Requirements: 4.1–4.8_

  - [ ] 2.6 Implement `ml/evaluator.py` — CV, hyperparameter tuning, and metrics
    - Perform k-fold CV with `Config.CV_FOLDS` (default 5)
    - Run hyperparameter tuning with `Config.HYPERPARAM_STRATEGY` (default grid, ≤50 candidates)
    - Compute accuracy, F1-weighted, precision-weighted, recall-weighted, ROC-AUC (OvR for ≤10 classes) per model
    - Record mean and std of F1-weighted across CV folds in evaluation report
    - On model failure: record error entry, continue
    - Return evaluation report to caller; no Flask or preprocessing imports
    - _Requirements: 5.1–5.7_

  - [ ] 2.7 Implement `ml/model_selector.py` — best model selection and serialization
    - Select model with highest F1-weighted; tie-break on precision-weighted then alphabetical name
    - Log selected model name, F1 score, and tie-break rationale
    - Log sorted summary table of all models by F1-weighted descending
    - Raise descriptive error if no valid F1 scores in report
    - Exclude models with missing F1 scores; log their names
    - Serialize best model and scaler to `Config.MODEL_REGISTRY_PATH` using `pickle` with UTC ISO 8601 timestamp in filename
    - Write `metadata.json` with model name, F1 score, and serialization timestamp
    - Create `saved_models/` directory if absent
    - Re-raise on I/O or permission error; log target path
    - Log paths of all serialized artifacts
    - _Requirements: 6.1–6.7, 7.1–7.6_

  - [ ] 2.8 Implement `scripts/train.py` — full pipeline entry point
    - Wire Ingestion → Preprocessor → EDAVisualizer → Split → Trainer → Evaluator → ModelSelector in sequence
    - Load config from env; exit with code 1 on any missing required variable
    - Write a lightweight status file (`saved_models/training_status.json`) with `{"status": "completed"|"failed", "timestamp": "..."}` at end of run (used by admin retrain status endpoint)
    - All error types (`ConfigurationError`, `DataIngestionError`, `DataParseError`) exit with code 1
    - _Requirements: 1.1–1.7, 2.1–2.10, 3.1–3.5, 4.1–4.8, 5.1–5.7, 6.1–6.7, 7.1–7.6_

- [ ] 3. Phase 3 — Prediction Engine
  - [ ] 3.1 Implement `app/models/` dataclasses: `InputVector`, `PredictionResult`, `PredictionRecord`, `SuitabilityResult`, `ModelMetadata`
    - `InputVector`: 7 float fields + `FIELD_RANGES` dict constant
    - `PredictionResult`: `predicted_label: str`, `confidence_score: float`
    - `PredictionRecord`: all 13 fields including `id: int | None` and `hashed_ip: str`
    - `SuitabilityResult`: `suitable`, `marginal`, `unsuitable` lists
    - `ModelMetadata`: 5 fields as shown in design
    - _Requirements: 8.4, 10.5, 12.2, 13.3_

  - [ ] 3.2 Implement `app/ml/prediction_engine.py` — `PredictionEngine` class
    - `__init__`: load model and scaler from `model_path` and `scaler_path` via `pickle.load`; raise `FileNotFoundError` with path if either is missing
    - `predict(input_vector: list[float]) -> PredictionResult`: apply scaler, run inference, return `PredictionResult`
    - Raise `ValueError` on wrong shape or non-numeric input
    - No Flask, database, or preprocessing imports
    - Importable standalone for scripts and tests
    - _Requirements: 8.1–8.9_

- [ ] 4. Phase 4 — Flask Application Foundation
  - [ ] 4.1 Implement `app/__init__.py` — `create_app()` application factory
    - Select config class from `FLASK_ENV`; log warning if absent, default to `ProductionConfig`
    - Validate required env vars; log error identifying missing var, exit with non-zero status if absent
    - Call `extensions.csrf.init_app(app)` and `extensions.limiter.init_app(app)`
    - Initialize logger; register all Blueprints
    - Check model artifact exists at startup; log WARNING with path if missing (do not halt)
    - Register global exception handler using `generate_correlation_id()`; return 500 with correlation ID
    - Register 404 and 500 error handlers
    - Log request method and path at INFO level via `@app.before_request`
    - _Requirements: 9.1, 9.5, 9.6, 9.7, 9.8, 16.2, 16.3, 17.1, 17.2, 17.3_

- [ ] 5. Phase 5 — Data Layer
  - [ ] 5.1 Implement `app/repositories/prediction_repository.py` — `PredictionRepository`
    - `__init__(db_path)`: open SQLite connection; run `CREATE TABLE IF NOT EXISTS predictions` with schema from design; create index on `timestamp DESC`
    - `save(record: PredictionRecord)`: INSERT all 13 fields; log ERROR and raise on DB write failure
    - `get_paginated(page, page_size) -> list[PredictionRecord]`: `ORDER BY timestamp DESC LIMIT ? OFFSET ?`
    - `count() -> int`: `SELECT COUNT(*) FROM predictions`
    - Store only `hashed_ip`; never accept or store raw IP
    - All SQL exclusively in this module
    - _Requirements: 12.1–12.6, 9.3_

- [ ] 6. Phase 6 — Service Layer
  - [ ] 6.1 Implement `app/validators/input_validator.py` — `InputValidator`
    - `validate(data: dict) -> InputVector | ValidationError`:
      - Check all 7 fields present → else 400-level `ValidationError` with field names
      - Parse each as `float` → else field-level "numeric required" error
      - Check each against `FIELD_RANGES` → else field-level range error
      - HTML-escape all string values before logging or storage using `html.escape()`
    - Return validated `InputVector` dataclass on success
    - _Requirements: 13.1–13.5, 10.2–10.4, 11.3–11.5_

  - [ ] 6.2 Implement `app/services/recommendation_service.py` — `RecommendationService`
    - Constructor: `(engine: PredictionEngine, repo: PredictionRepository)`
    - `recommend(input_vector: InputVector, hashed_ip: str) -> PredictionResult`
    - Invoke `engine.predict()`, call `repo.save()` with complete `PredictionRecord`, return result
    - Never call `SuitabilityService` or share service code with it
    - Log INFO with input field values and predicted crop (no raw IP)
    - _Requirements: 10.1, 10.5, 10.6, 17.4_

  - [ ] 6.3 Implement `app/services/suitability_service.py` — `SuitabilityService`
    - Constructor: `(config: BaseConfig)`
    - `evaluate(input_vector: InputVector) -> SuitabilityResult`
    - Parse `Config.SUITABILITY_THRESHOLDS` JSON; evaluate each crop as suitable/marginal/unsuitable
    - Every crop in config appears in exactly one tier
    - Never invoke `PredictionEngine` or `RecommendationService`
    - _Requirements: 11.1, 11.2, 11.6, 11.7_

  - [ ] 6.4 Implement `app/services/dashboard_service.py` — `DashboardService`
    - Aggregate from `PredictionRepository`: total count, most recommended crop, avg confidence, daily counts for last 30 days
    - Return structured dict matching `GET /api/dashboard` response schema
    - _Requirements: 21.1_

  - [ ] 6.5 Implement `app/services/analytics_service.py` — `AnalyticsService`
    - Aggregate: model scores from `metadata.json`, daily prediction volumes, crop distribution from repository
    - Return structured dict matching `GET /api/analytics` response schema
    - _Requirements: 22.1–22.3_

  - [ ] 6.6 Implement `app/services/admin_service.py` — `AdminService`
    - `get_model_metadata() -> ModelMetadata`: read `metadata.json` from `Model_Registry`
    - `get_system_health() -> SystemHealth`: uptime, total prediction count, DB file size in MB, last training timestamp
    - `get_retrain_status() -> dict`: read `saved_models/training_status.json`; return `{"status": "...", "timestamp": "..."}`
    - `trigger_retraining()`: spawn `threading.Thread` running `subprocess.run(["python", "scripts/train.py"])` as daemon; log error if non-zero return code; never block the request
    - _Requirements: 25.2, 25.3, 25.4, 25.6_

  - [ ] 6.7 Implement admin session authentication — `@login_required` decorator and bcrypt verification
    - Create `app/utils/auth.py` with `login_required` decorator that checks `session['admin_logged_in']`; redirects unauthenticated users to `/admin/login` with 302
    - Implement `verify_admin(username, password)` using `bcrypt.checkpw` against `Config.ADMIN_PASSWORD_HASH`
    - _Requirements: 25.1_

- [ ] 7. Phase 7 — Controllers
  - [ ] 7.1 Implement `app/controllers/recommendation_controller.py`
    - Parse JSON body, call `InputValidator.validate()`, call `RecommendationService.recommend()`, return 200 JSON
    - Return 400 with field-level errors on `ValidationError`
    - Return 500 with sanitized message + correlation ID on engine or repo errors (no stack traces or paths in response)
    - _Requirements: 10.3, 10.4, 10.7, 10.8, 17.2_

  - [ ] 7.2 Implement `app/controllers/suitability_controller.py`
    - Parse body, validate, call `SuitabilityService.evaluate()`, return 200 JSON
    - Return 400 with field-level errors on `ValidationError`
    - _Requirements: 11.3–11.5_

  - [ ] 7.3 Implement `app/controllers/history_controller.py`
    - Accept `page` (default 1) and `page_size` (default 25, max 100) query params
    - Call `PredictionRepository.get_paginated()` and `.count()`; return paginated response
    - Exclude `hashed_ip` from all response records
    - _Requirements: 24.1–24.5_

  - [ ] 7.4 Implement `app/controllers/dashboard_controller.py` and `app/controllers/analytics_controller.py`
    - Each calls the respective service and returns JSON matching the API spec
    - _Requirements: 21.1, 22.1–22.3_

  - [ ] 7.5 Implement `app/controllers/admin_controller.py`
    - `get_metadata()`: call `AdminService.get_model_metadata()`
    - `post_retrain()`: call `AdminService.trigger_retraining()`; return 202
    - `get_retrain_status()`: call `AdminService.get_retrain_status()`; return JSON
    - `admin_login_post()`: call `verify_admin()`; set `session['admin_logged_in'] = True` on success; redirect to `/admin`; return 401 on failure
    - `admin_logout()`: clear session; redirect to `/`
    - _Requirements: 25.1–25.6_

- [ ] 8. Phase 8 — Routes & Blueprints
  - [ ] 8.1 Implement `app/routes/main_routes.py` — page routes and health check
    - `GET /` → render `index.html`
    - `GET /about` → render `about.html`
    - `GET /contact` → render `contact.html`
    - `GET /research` → render `research.html`
    - `GET /api/health` → return `{"status": "ok", "uptime_seconds": <int>}` with HTTP 200
    - _Requirements: 18.1, 26.1, 26.2, 9.1_

  - [ ] 8.2 Implement `app/routes/recommendation_routes.py`
    - `GET /recommend` → render `recommend.html`
    - `POST /api/recommend` → delegate to `recommendation_controller`; apply rate limiter from `Config.RECOMMEND_RATE_LIMIT`
    - Return 429 with `Retry-After` header on limit exceeded
    - _Requirements: 10.1–10.8, 15.1, 15.3, 15.4_

  - [ ] 8.3 Implement `app/routes/suitability_routes.py`
    - `GET /suitability` → render `suitability.html`
    - `POST /api/suitability` → delegate to `suitability_controller`; apply rate limiter from `Config.SUITABILITY_RATE_LIMIT`
    - Return 429 with `Retry-After` header on limit exceeded
    - _Requirements: 11.1–11.7, 15.2, 15.3, 15.4_

  - [ ] 8.4 Implement `app/routes/history_routes.py`, `app/routes/dashboard_routes.py`, `app/routes/analytics_routes.py`
    - History: `GET /history` → `history.html`; `GET /api/history` → `history_controller`
    - Dashboard: `GET /dashboard` → `dashboard.html`; `GET /api/dashboard` → `dashboard_controller`
    - Analytics: `GET /analytics` → `analytics.html`; `GET /api/analytics` → `analytics_controller`
    - _Requirements: 21.1–21.6, 22.1–22.5, 24.1–24.5_

  - [ ] 8.5 Implement `app/routes/admin_routes.py` — admin Blueprint
    - `GET /admin` → `admin/dashboard.html` (login_required)
    - `GET /admin/login` → `admin/login.html`
    - `POST /admin/login` → `admin_controller.admin_login_post()`
    - `GET /admin/logout` → `admin_controller.admin_logout()`
    - `GET /api/admin/metadata` → `admin_controller.get_metadata()` (login_required)
    - `POST /api/admin/retrain` → `admin_controller.post_retrain()` (login_required)
    - `GET /api/admin/retrain/status` → `admin_controller.get_retrain_status()` (login_required)
    - All admin routes require `@login_required` except `/admin/login`
    - _Requirements: 25.1–25.6_

  - [ ] 8.6 Register all Blueprints in `app/__init__.py`
    - Import and call `app.register_blueprint()` for each Blueprint created in 8.1–8.5
    - _Requirements: 9.1_

- [ ] 9. Phase 9 — Frontend
  - [ ] 9.1 Implement `app/static/css/main.css` and `app/templates/base.html`
    - `main.css`: define CSS custom properties for dark/light mode (`--bg-color`, `--text-color`, etc.); Bootstrap 5 override rules; responsive breakpoint assertions
    - `base.html`: Bootstrap 5 CDN, Bootstrap Icons CDN, navbar with links to all pages, dark/light mode toggle control (reads `data-bs-theme`), CSRF meta tag, block slots for `title`, `content`, `extra_js`; viewport meta tag
    - _Requirements: 18.2, 18.4, 31.7, 31.8, 31.9_

  - [ ] 9.2 Implement `app/static/js/theme.js` and `app/static/js/loading.js`
    - `theme.js`: read `localStorage['opticrop-theme']` on DOM load; apply `data-bs-theme` to `<html>`; register toggle handler; update `localStorage` and CSRF header on change
    - `loading.js`: export `showLoading(btn, form)` and `hideLoading(btn, form)` utilities
    - _Requirements: 18.4, 19.3_

  - [ ] 9.3 Implement `app/static/js/validation.js`
    - Mirror server-side `FIELD_RANGES` for all 7 fields
    - On submit: check numeric type and range; block submission; render inline field-level errors
    - Clear errors on field change
    - _Requirements: 13.5, 19.2_

  - [ ] 9.4 Implement `app/templates/index.html` — Home page
    - Hero section with headline and CTA button navigating to `/recommend`
    - Feature highlights section (at least 3 feature cards)
    - Apply Bootstrap 5 responsive grid (col-xs through col-xl)
    - On `DOMContentLoaded`: add CSS animation classes to hero and feature elements (transition to visible within 800ms)
    - _Requirements: 18.1–18.4_

  - [ ] 9.5 Implement `app/templates/recommend.html` and submit flow
    - Form with 7 labeled inputs, unit hint text, and valid range hint per field
    - On submit: show loading spinner via `loading.js`, disable submit button
    - On 200 success: display predicted crop name, confidence score as percentage (1 decimal), agronomic notes
    - On 400: display field-level error messages per field
    - On 500: display user-friendly error alert with correlation ID (no stack trace)
    - _Requirements: 19.1–19.6_

  - [ ] 9.6 Implement `app/templates/suitability.html`
    - 7-field form with unit and range hints
    - Display results grouped by tier: suitable (green), marginal (amber), unsuitable (red)
    - Distinct heading and color scheme from recommend page
    - Loading indicator and button disable on submit; error display on failure
    - _Requirements: 20.1–20.6_

  - [ ] 9.7 Implement `app/static/js/charts.js` — Chart.js wrappers
    - Export `renderBarChart(canvasId, labels, data, options)`, `renderLineChart(...)`, `renderPieChart(...)`
    - Graceful fallback: if Chart.js CDN fails to load, display "Unavailable" message in canvas container
    - Source Chart.js URL from the `CHARTJS_URL` Jinja2 variable injected by the base template
    - _Requirements: 21.2, 21.6_

  - [ ] 9.8 Implement `app/static/js/dashboard.js` and `app/templates/dashboard.html`
    - `dashboard.js`: fetch `/api/dashboard`; on load render KPI cards and activity line chart; show skeleton loaders during fetch; on error replace each failed widget with error message
    - `dashboard.html`: Bootstrap grid with KPI card skeletons and chart canvas; inject `CHARTJS_URL` config
    - _Requirements: 21.1–21.6_

  - [ ] 9.9 Implement `app/static/js/analytics.js` and `app/templates/analytics.html`
    - `analytics.js`: fetch `/api/analytics`; render model comparison bar chart, daily volume line chart, crop distribution pie chart; loading indicators; "Data unavailable" placeholder on failure
    - `analytics.html`: chart canvas elements; Bootstrap responsive grid
    - _Requirements: 22.1–22.5_

  - [ ] 9.10 Implement `app/templates/history.html`
    - Paginated table: timestamp, N, P, K, temperature, humidity, rainfall, pH, predicted crop, confidence score, model name
    - No raw IP or hashed IP shown
    - Empty-state message when no records
    - Loading indicator and disabled pagination controls during fetch
    - _Requirements: 24.1–24.5_

  - [ ] 9.11 Implement `app/templates/research.html`
    - Display correlation heatmap, class distribution, and per-feature histograms using `<img>` tags pointing to `app/static/eda/`
    - If image fails to load (`onerror`): replace with descriptive placeholder text
    - Dataset summary statistics section (total rows, total columns, per-class counts) fetched from an inline Jinja2 context variable
    - Display error message if stats unavailable
    - _Requirements: 23.1–23.5_

  - [ ] 9.12 Implement `app/templates/about.html`, `app/templates/contact.html`, `app/templates/admin/login.html`, `app/templates/admin/dashboard.html`, `app/templates/admin/logs.html`
    - `about.html`: platform purpose, ML methodology, tech stack (all libraries from requirements.txt)
    - `contact.html`: name, email, message form; client-side required-field validation; block submit if any field empty
    - `admin/login.html`: username/password form with CSRF token hidden input
    - `admin/dashboard.html`: active model name, F1 score, serialization timestamp; retrain button with status indicator (pending/in-progress/completed/failed); JS polling of `/api/admin/retrain/status`; paginated prediction log table; system health metrics (uptime, count, DB size, last training timestamp)
    - `admin/logs.html`: paginated prediction records table showing hashed_ip, not raw IP
    - _Requirements: 25.2–25.6, 26.1–26.3_

  - [ ] 9.13 Implement `app/templates/errors/404.html` and `app/templates/errors/500.html`
    - Both extend `base.html`
    - 404: "Page not found" message + Home link to `/`
    - 500: "Server error" message + correlation ID + Home link to `/`
    - _Requirements: 27.1–27.3_

- [ ] 10. Phase 10 — Security Hardening
  - [ ] 10.1 Wire CSRF protection into all state-changing routes and templates
    - Confirm `CSRFProtect(app)` is active for all POST/PUT/PATCH/DELETE routes
    - Add `{{ csrf_token() }}` hidden input to every HTML form in templates
    - Add `X-CSRFToken` header in all fetch/XHR calls in JS modules
    - Verify 403 response is returned for requests missing the token
    - Source CSRF secret from `Config.CSRF_SECRET_KEY`; if absent at startup halt with error
    - _Requirements: 14.1–14.4_

  - [ ] 10.2 Verify and harden rate limiting on prediction endpoints
    - Confirm `@limiter.limit(Config.RECOMMEND_RATE_LIMIT)` on `POST /api/recommend`
    - Confirm `@limiter.limit(Config.SUITABILITY_RATE_LIMIT)` on `POST /api/suitability`
    - Write custom 429 error handler returning `{"error": "rate_limit_exceeded", "retry_after": <int>}` and `Retry-After` header
    - Confirm window reset clears counter to zero
    - _Requirements: 15.1–15.6_

  - [ ] 10.3 Verify IP hashing and privacy controls end-to-end
    - Trace request path to confirm `sha256_ip(request.remote_addr)` is called before any persistence
    - Verify raw IP is absent from all log statements, DB columns, and API responses
    - _Requirements: 12.3, 17.4, 17.5_

- [ ] 11. Phase 11 — Testing
  - [ ] 11.1 Write `tests/conftest.py` — shared fixtures
    - `app` fixture: `create_app(TestingConfig)` with in-memory SQLite (`DATABASE_PATH=":memory:"`)
    - `client` fixture: `app.test_client()`
    - `mock_engine` fixture: `unittest.mock.patch` on `PredictionEngine.predict` returning `PredictionResult(predicted_label="rice", confidence_score=0.95)`
    - _Requirements: 28.1_

  - [ ] 11.2 Write `tests/test_recommendation_routes.py` — route-level tests
    - Test 200 with valid payload (all 7 fields in range); assert JSON has `predicted_crop`, `confidence_score`, `model_name`
    - Test 400 on missing field (each field individually); assert field-level error in `fields` key
    - Test 400 on non-numeric field; assert field-level error
    - Test 400 on out-of-range value for each field; assert field name and range in error
    - Test 403 on missing CSRF token
    - _Requirements: 28.2, 28.4_

  - [ ] 11.3 Write `tests/test_suitability_routes.py`
    - Test 200 with valid payload; assert `suitable`, `marginal`, `unsuitable` keys in response
    - Test 400 on missing fields and out-of-range values
    - Test 403 on missing CSRF token
    - _Requirements: 28.2, 28.4_

  - [ ] 11.4 Write `tests/test_history_routes.py`
    - Test 200 with populated DB; assert paginated response shape
    - Test default pagination (page=1, page_size=25)
    - Test empty DB returns empty records array
    - Test `hashed_ip` absent from response records
    - _Requirements: 28.2_

  - [ ] 11.5 Write `tests/test_admin_routes.py`
    - Test redirect to `/admin/login` for unauthenticated requests
    - Test login with correct credentials sets session; test with wrong credentials returns 401
    - Test logout clears session
    - Test `/api/admin/retrain` returns 202 (mock `trigger_retraining`)
    - _Requirements: 28.2_

  - [ ] 11.6 Write `tests/test_prediction_engine.py`
    - Test `PredictionEngine.__init__` raises `FileNotFoundError` with path when model file missing
    - Test `PredictionEngine.__init__` raises `FileNotFoundError` with path when scaler file missing
    - Test `predict()` raises `ValueError` on wrong-shape input
    - Test `predict()` raises `ValueError` on non-numeric input
    - Test `predict()` returns `PredictionResult` with non-empty `predicted_label` and `confidence_score` in [0.0, 1.0] using mocked model
    - _Requirements: 28.3_

  - [ ] 11.7 Write `tests/test_prediction_repository.py`
    - Use in-memory SQLite; test `save()` persists all 13 fields
    - Test `get_paginated()` returns records in descending timestamp order
    - Test `count()` returns correct total after multiple saves
    - Test `save()` raises and logs on DB error (simulated via patching)
    - _Requirements: 28.5_

  - [ ] 11.8 Write `tests/test_input_validator.py`
    - Test each of the 7 fields individually for: missing, non-numeric, below min, above max
    - Test valid payload passes without error
    - Test HTML characters in string values are escaped before return
    - _Requirements: 28.4_

  - [ ] 11.9 Write `tests/test_model_selector.py`
    - Test highest F1 model is selected
    - Test precision-weighted tie-break
    - Test alphabetical tie-break
    - Test missing F1 scores are excluded and logged
    - Test error raised when no valid scores exist
    - _Requirements: 28.2_

  - [ ] 11.10 Write `tests/test_preprocessor.py`
    - Test step ordering (mock each step; assert call order)
    - Test duplicate removal reduces row count correctly
    - Test outlier treatment with IQR clip strategy
    - Test feature scaling returns scaled DataFrame + fitted scaler
    - Test raises on invalid missing value strategy
    - _Requirements: 28.2_

  - [ ] 11.11 Write `tests/test_recommendation_service.py` and `tests/test_suitability_service.py`
    - `test_recommendation_service.py`: mock engine + repo; assert engine.predict called; assert repo.save called with matching fields; assert hashed_ip stored
    - `test_suitability_service.py`: assert every configured crop appears in exactly one tier; assert no crop appears in two tiers
    - _Requirements: 28.2_

  - [ ] 11.12 Write `tests/property/conftest.py` and Hypothesis strategies
    - Define `valid_input_vectors()`, `dataframes_with_missing_values()`, `dataframes_with_duplicates()`, `arbitrary_labeled_dataframes()`, `crop_dataframes()`, `evaluation_reports()`, `prediction_records()`, `out_of_range_value_for_field()` strategies
    - _Requirements: 28.1_

  - [ ]* 11.13 Write `tests/property/test_prop_preprocessor.py`
    - **Property 1: Missing value handling completeness** — `@given(df=dataframes_with_missing_values()) @settings(max_examples=100)` — after processing, resulting DataFrame contains zero missing values; logged count equals N
    - **Property 2: Duplicate row removal count correctness** — `@given(df=dataframes_with_duplicates()) @settings(max_examples=100)` — row count after dedup equals `original - D`; logged count equals D
    - **Property 3: Class distribution counts sum to total rows** — `@given(df=arbitrary_labeled_dataframes()) @settings(max_examples=100)` — per-class counts sum to total DataFrame row count
    - _Requirements: 2.2, 2.3, 2.7_

  - [ ]* 11.14 Write `tests/property/test_prop_split.py` (trains/test split properties)
    - **Property 4: Train/test split proportionality and class preservation** — `@given(dataset=crop_dataframes(), ratio=st.floats(min_value=0.01, max_value=0.49)) @settings(max_examples=100)` — test set size is `floor(N * r)`; each class relative frequency within 5%
    - **Property 5: Split determinism under same seed** — `@given(dataset=crop_dataframes(), seed=st.integers(min_value=0, max_value=2**32-1)) @settings(max_examples=100)` — two calls with same seed produce element-wise identical sets
    - _Requirements: 3.1, 3.3, 3.4_

  - [ ]* 11.15 Write `tests/property/test_prop_model_selector.py`
    - **Property 6: Model selection picks max-F1 with tie-breaking** — `@given(report=evaluation_reports()) @settings(max_examples=100)` — selected model has max F1; precision tie-break; alphabetical final tie-break; invalid scores excluded
    - _Requirements: 6.1, 6.2, 6.6_

  - [ ]* 11.16 Write `tests/property/test_prop_prediction_engine.py`
    - **Property 7: Prediction engine result structure validity** — `@given(input_vec=valid_input_vectors()) @settings(max_examples=100)` — `predicted_label` is non-empty string; `confidence_score` in [0.0, 1.0]
    - **Property 15: Predicted label belongs to training label set** — same strategy — `predicted_label` is a member of known crop labels
    - **Property 16: Scaler round-trip preserves input values** — `@given(input_vec=valid_input_vectors()) @settings(max_examples=100)` — `inverse_transform(transform(v))` within 1e-6 of original values
    - _Requirements: 8.4, 28.3, 28.7, 28.8_

  - [ ]* 11.17 Write `tests/property/test_prop_validation.py`
    - **Property 8: Valid input returns valid prediction response** — `@given(input_vec=valid_input_vectors()) @settings(max_examples=100)` — HTTP 200; response has `predicted_crop`, `confidence_score`, `model_name`
    - **Property 9: Missing field returns 400 with field-level error** — `@given(missing_fields=st.sets(...)) @settings(max_examples=100)` — 400; `fields` object contains entry for each missing field only
    - **Property 10: Out-of-range field returns 400 with field and range** — `@given(...) @settings(max_examples=100)` — 400; `fields` identifies offending field and valid range
    - _Requirements: 10.1, 10.3, 10.4_

  - [ ]* 11.18 Write `tests/property/test_prop_repository.py`
    - **Property 11: Prediction record persisted with all input fields** — `@given(record=prediction_records()) @settings(max_examples=100)` — fields in retrieved record match saved record exactly
    - **Property 12: Every crop in exactly one suitability tier** — `@given(input_vec=valid_input_vectors()) @settings(max_examples=100)` — `suitable ∪ marginal ∪ unsuitable` equals full crop set; sets pairwise disjoint
    - **Property 13: Paginated records ordered by timestamp descending** — `@given(records=st.lists(...)) @settings(max_examples=100)` — adjacent records in result satisfy `timestamp[i] >= timestamp[i+1]`
    - **Property 14: Count equals persisted record count** — `@given(records=st.lists(...)) @settings(max_examples=100)` — `count()` equals number of successful `save()` calls
    - _Requirements: 10.5, 11.1, 12.4, 12.5_

  - [ ] 11.19 Checkpoint — ensure all tests pass
    - Run `pytest tests/ --cov=app --cov=ml --cov-report=term-missing`; verify branch coverage ≥ 80%
    - Fix any failing tests before proceeding to Phase 12
    - Ask the user if any questions arise.

- [ ] 12. Phase 12 — Deployment
  - [ ] 12.1 Write `Dockerfile`
    - `FROM python:3.11-slim`; `WORKDIR /app`; copy `requirements.txt` and install; copy source; create runtime dirs (`logs`, `instance`, `saved_models`, `datasets`, `app/static/eda`); `EXPOSE 5000`; `CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]`
    - _Requirements: 29.1_

  - [ ] 12.2 Write `docker-compose.yml`
    - Service `web`: build `.`; ports `5000:5000`; `env_file: .env`; named volumes for `datasets`, `saved_models`, `logs`, `instance`
    - Health check: `GET http://localhost:5000/api/health`; interval 10s; timeout 5s; retries 3; start_period 15s
    - _Requirements: 29.2, 29.6_

  - [ ] 12.3 Write `gunicorn.conf.py`
    - `bind = "0.0.0.0:5000"`; `workers = min(int(os.environ.get("GUNICORN_WORKERS", "4")), 8)`; `timeout = 120`; `loglevel` from `LOG_LEVEL`; `accesslog = "-"`; `errorlog = "-"`
    - _Requirements: 29.3, 29.5_

- [ ] 13. Phase 13 — Documentation
  - [ ] 13.1 Write `README.md`
    - Overview, prerequisites, quick-start for local venv and Docker, link to all `docs/*.md` files
    - _Requirements: 30.1_

  - [ ] 13.2 Write `docs/installation.md`
    - Step-by-step: create venv, install requirements, configure `.env`, run `scripts/train.py`, start Flask; Docker equivalent
    - _Requirements: 30.2_

  - [ ] 13.3 Write `docs/architecture.md`
    - Describe all clean architecture layers, each module's responsibility, end-to-end data flow through ML pipeline and Flask app; include component diagram reference
    - _Requirements: 30.3_

  - [ ] 13.4 Write `docs/api.md`
    - Document every HTTP endpoint: method, URL, request body, success response schema, all error codes and messages
    - _Requirements: 30.4_

  - [ ] 13.5 Write `docs/deployment.md` and `docs/docker.md`
    - `deployment.md`: production env var setup, Gunicorn worker tuning, log rotation
    - `docker.md`: image build, container run, volume config, port mapping, Docker Compose networking
    - _Requirements: 30.5, 30.6_

- [ ] 14. Final Checkpoint
  - Run full test suite and verify all tests pass; run `docker-compose build` to verify the image builds without errors.
  - Ensure all tests pass; ask the user if questions arise.


## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; all other tasks are required.
- Each task references specific requirements for traceability.
- Property tests in Phase 11 use `Hypothesis` with `@settings(max_examples=100)` per property.
- The ML pipeline (Phase 2) and Flask app (Phases 3–10) are fully decoupled; `ml/` modules must never import from `app/`, and vice versa.
- Admin password hash must be pre-generated with `bcrypt` and placed in `ADMIN_PASSWORD_HASH` env var before first run.
- `scripts/train.py` must be executed at least once before the Flask app serves predictions (to produce model artifacts in `saved_models/`).
- All module files must stay under 300 lines; all functions under 50 lines per Requirement 31.10.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "1.6", "1.7", "1.8"]
    },
    {
      "id": 1,
      "tasks": ["1.2", "1.3", "1.4", "1.5"]
    },
    {
      "id": 2,
      "tasks": ["2.1", "3.1"]
    },
    {
      "id": 3,
      "tasks": ["2.2", "2.3", "3.2"]
    },
    {
      "id": 4,
      "tasks": ["2.4"]
    },
    {
      "id": 5,
      "tasks": ["2.5"]
    },
    {
      "id": 6,
      "tasks": ["2.6"]
    },
    {
      "id": 7,
      "tasks": ["2.7"]
    },
    {
      "id": 8,
      "tasks": ["2.8", "4.1"]
    },
    {
      "id": 9,
      "tasks": ["5.1", "6.1"]
    },
    {
      "id": 10,
      "tasks": ["6.2", "6.3", "6.4", "6.5", "6.6", "6.7"]
    },
    {
      "id": 11,
      "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5"]
    },
    {
      "id": 12,
      "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5"]
    },
    {
      "id": 13,
      "tasks": ["8.6"]
    },
    {
      "id": 14,
      "tasks": ["9.1"]
    },
    {
      "id": 15,
      "tasks": ["9.2", "9.3"]
    },
    {
      "id": 16,
      "tasks": ["9.4", "9.5", "9.6", "9.7"]
    },
    {
      "id": 17,
      "tasks": ["9.8", "9.9", "9.10", "9.11"]
    },
    {
      "id": 18,
      "tasks": ["9.12", "9.13"]
    },
    {
      "id": 19,
      "tasks": ["10.1", "10.2", "10.3"]
    },
    {
      "id": 20,
      "tasks": ["11.1"]
    },
    {
      "id": 21,
      "tasks": ["11.2", "11.3", "11.4", "11.5", "11.6", "11.7", "11.8", "11.9", "11.10", "11.11", "11.12"]
    },
    {
      "id": 22,
      "tasks": ["11.13", "11.14", "11.15", "11.16", "11.17", "11.18"]
    },
    {
      "id": 23,
      "tasks": ["12.1", "12.2", "12.3"]
    },
    {
      "id": 24,
      "tasks": ["13.1", "13.2", "13.3", "13.4", "13.5"]
    }
  ]
}
```
