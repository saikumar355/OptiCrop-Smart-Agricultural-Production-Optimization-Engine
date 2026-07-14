# Project Demonstration Guide — OptiCrop AI

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
python -m dotenv run python wsgi.py
```

### 3. Open browser
```
http://127.0.0.1:5000
```

---

## Demo Walkthrough

### Step 1 — Home Page (`/`)
- Shows platform overview, feature cards, and stats
- 9 ML algorithms, 22 crop classes, F1-optimized model selection
- Click **Get Recommendation** to proceed

---

### Step 2 — Crop Recommendation (`/recommend`)

Enter these sample values to get a **rice** prediction:

| Field | Value |
|---|---|
| Nitrogen (N) | 90 |
| Phosphorus (P) | 42 |
| Potassium (K) | 43 |
| Temperature | 20.8 |
| Humidity | 82 |
| Rainfall | 202.9 |
| pH | 6.5 |

Expected result: **rice** with ~54% confidence (ExtraTrees model)

Try these for **maize**:

| Field | Value |
|---|---|
| N | 77 |
| P | 52 |
| K | 17 |
| Temperature | 22 |
| Humidity | 82 |
| Rainfall | 85 |
| pH | 6.5 |

---

### Step 3 — Suitability Analysis (`/suitability`)
- Uses the same 7-field form
- Returns crops grouped into **Suitable / Marginal / Unsuitable** tiers
- Based on agronomic threshold rules, NOT the ML model
- Note: requires `SUITABILITY_THRESHOLDS` in `.env` to show results

---

### Step 4 — Prediction History (`/history`)
- Shows all predictions made so far in a paginated table
- Columns: crop, N/P/K/temp/humidity/rainfall/pH, confidence, model, date
- Raw IP is never shown — SHA-256 hash only (privacy compliant)

---

### Step 5 — Dashboard (`/dashboard`)
- KPI cards: Total Predictions, Avg Confidence, Most Recommended Crop
- Daily prediction volume line chart (last 30 days)
- All data loaded live from `/api/dashboard`

---

### Step 6 — Analytics (`/analytics`)
- Model F1 score bar chart
- Crop distribution doughnut chart
- Daily prediction volume line chart
- Active model name and F1 score card

---

### Step 7 — Research (`/research`)
- EDA plots generated during model training:
  - Correlation heatmap (feature relationships)
  - Class distribution (22 crops, balanced at 100 each)
  - 7 feature histograms (N, P, K, temp, humidity, rainfall, pH)
- Dataset stats: 2200 rows, 8 columns

---

### Step 8 — Admin Panel (`/admin/login`)

Login credentials:
- **Username:** `admin`
- **Password:** `10471047`

Admin features:
- Full prediction log table with every record
- Delete individual records or clear all history
- Trigger background model retraining
- View active model metadata (name, F1 score, timestamp)
- System health: uptime, DB size, total predictions

---

## API Demo (curl / Postman)

### Make a prediction
```bash
curl -X POST http://127.0.0.1:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"N":90,"P":42,"K":43,"temperature":20.8,"humidity":82,"rainfall":202.9,"ph":6.5}'
```

Expected response:
```json
{
  "predicted_crop": "rice",
  "confidence_score": 0.54,
  "model_name": "ExtraTrees_2026-07-01T122126Z"
}
```

### Health check
```bash
curl http://127.0.0.1:5000/api/health
```

### Prediction history
```bash
curl "http://127.0.0.1:5000/api/history?page=1&page_size=5"
```

---

## Key Technical Features to Highlight

| Feature | Where to show |
|---|---|
| ML model comparison (9 algorithms) | `ml/trainer.py`, `ml/evaluator.py` |
| Best model selection by F1 | `ml/model_selector.py` |
| Clean architecture (5 layers) | `app/routes/`, `app/controllers/`, `app/services/`, `app/repositories/` |
| PredictionEngine singleton (performance) | `app/__init__.py` extensions |
| SHA-256 IP hashing (privacy) | `app/utils/hashing.py` |
| CSRF + rate limiting (security) | `app/extensions.py`, route decorators |
| Property-based testing | `tests/property/` — 27 tests with Hypothesis |
| Docker deployment | `Dockerfile`, `docker-compose.yml` |
| 103 tests, all passing | `tests/` directory |
