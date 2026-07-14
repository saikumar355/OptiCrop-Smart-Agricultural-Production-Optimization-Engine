# API Reference

All JSON endpoints are prefixed with `/api`. HTML page routes are served separately by Flask + Jinja2 templates.

Authentication for admin endpoints uses session-based login. Obtain a session by `POST /admin/login` before calling protected routes.

---

## Input Vector

Seven fields are required by all prediction and suitability endpoints:

| Field | Type | Valid Range | Unit |
|---|---|---|---|
| `N` | float | [0, 140] | kg/ha |
| `P` | float | [5, 145] | kg/ha |
| `K` | float | [5, 205] | kg/ha |
| `temperature` | float | [0, 50] | °C |
| `humidity` | float | [0, 100] | % |
| `rainfall` | float | [0, 300] | mm |
| `ph` | float | [0, 14] | — |

---

## Common Error Responses

### 400 — Validation Error

```json
{
  "error": "validation_error",
  "fields": {
    "N": "Field is required.",
    "ph": "Value 15.0 is outside valid range [0, 14]."
  }
}
```

### 429 — Rate Limit Exceeded

```json
{
  "error": "rate_limit_exceeded",
  "retry_after": 47
}
```

Includes a `Retry-After` header with the remaining window duration in seconds.

### 500 — Internal Error

```json
{
  "error": "internal_error",
  "correlation_id": "a3f9b2c1"
}
```

Stack traces, file paths, and environment variable values are never included.

---

## Endpoints

---

### POST /api/recommend

Invoke the ML model and receive a crop recommendation.

**Auth required:** No

**Rate limited:** Yes (default: 20 per minute per IP)

**Request body (JSON):**

```json
{
  "N": 90.0,
  "P": 42.0,
  "K": 43.0,
  "temperature": 20.8,
  "humidity": 82.0,
  "rainfall": 202.9,
  "ph": 6.5
}
```

**Success 200:**

```json
{
  "predicted_crop": "rice",
  "confidence_score": 0.953,
  "model_name": "ExtraTrees_2026-07-01T122126Z"
}
```

| Field | Type | Description |
|---|---|---|
| `predicted_crop` | string | Recommended crop name |
| `confidence_score` | float [0.0, 1.0] | Model confidence in the prediction |
| `model_name` | string | Name and timestamp of the active model |

**Errors:** 400 (missing/invalid field), 429 (rate limit), 500 (inference or persistence failure)

---

### POST /api/suitability

Threshold-based suitability analysis for all configured crops. Does not use the ML model.

**Auth required:** No

**Rate limited:** Yes (default: 20 per minute per IP)

**Request body (JSON):** Same structure as `/api/recommend`.

**Success 200:**

```json
{
  "suitable":   ["rice", "coconut"],
  "marginal":   ["maize", "banana"],
  "unsuitable": ["apple", "grapes"]
}
```

Every crop defined in config appears in exactly one of the three tiers. The tiers are pairwise disjoint.

**Errors:** 400 (missing/invalid field), 429 (rate limit), 500

---

### GET /api/history

Paginated prediction history ordered by timestamp descending.

**Auth required:** No

**Query parameters:**

| Parameter | Type | Default | Max | Description |
|---|---|---|---|---|
| `page` | int | 1 | — | Page number (1-indexed) |
| `page_size` | int | 25 | 100 | Records per page |

**Example request:**

```
GET /api/history?page=2&page_size=10
```

**Success 200:**

```json
{
  "records": [
    {
      "id": 42,
      "timestamp": "2024-01-15T10:30:00Z",
      "N": 90.0,
      "P": 42.0,
      "K": 43.0,
      "temperature": 20.8,
      "humidity": 82.0,
      "rainfall": 202.9,
      "ph": 6.5,
      "predicted_crop": "rice",
      "confidence_score": 0.953,
      "model_name": "ExtraTrees_2026-07-01T122126Z"
    }
  ],
  "total": 150,
  "page": 2,
  "page_size": 10
}
```

`hashed_ip` is never returned to the client.

**Errors:** 500

---

### GET /api/dashboard

Summary statistics for the dashboard page.

**Auth required:** No

**Success 200:**

```json
{
  "total_predictions": 1500,
  "most_recommended_crop": "rice",
  "avg_confidence": 0.872,
  "daily_counts": [
    { "date": "2024-01-15", "count": 42 }
  ]
}
```

**Errors:** 500

---

### GET /api/analytics

Model comparison and prediction trend data for the analytics page.

**Auth required:** No

**Success 200:**

```json
{
  "model_scores": [
    { "model": "ExtraTrees", "f1_weighted": 0.989 }
  ],
  "daily_volumes": [
    { "date": "2024-01-15", "count": 42 }
  ],
  "crop_distribution": [
    { "crop": "rice", "count": 210 }
  ]
}
```

**Errors:** 500

---

### GET /api/health

Liveness probe for Docker health checks and load balancers. Always returns 200 as long as the process is running, even if no model is loaded.

**Auth required:** No

**Success 200:**

```json
{
  "status": "ok",
  "uptime_seconds": 3600
}
```

---

### GET /api/admin/metadata

Returns metadata for the currently active model.

**Auth required:** Yes (admin session)

**Success 200:**

```json
{
  "model_name": "ExtraTrees_2026-07-01T122126Z",
  "f1_weighted": 0.930,
  "serialization_timestamp": "2026-07-01T12:21:26Z",
  "model_path": "saved_models/ExtraTrees_2026-07-01T122126Z.pkl",
  "scaler_path": "saved_models/scaler_2026-07-01T122126Z.pkl"
}
```

**Errors:** 401/403 (unauthenticated), 500

---

### POST /api/admin/retrain

Triggers a background retraining job. The pipeline (`scripts/train.py`) runs in a daemon thread; the endpoint returns immediately.

**Auth required:** Yes (admin session)

**Request body:** Empty (no body required)

**Success 202:**

```json
{
  "status": "accepted",
  "message": "Retraining started in background."
}
```

**Errors:** 401/403 (unauthenticated), 500 (failed to spawn thread)

---

### GET /api/admin/retrain/status

Returns the current status of the most recent retraining job.

**Auth required:** Yes (admin session)

**Success 200:**

```json
{
  "status": "running"
}
```

Possible `status` values: `"idle"`, `"running"`, `"completed"`, `"failed"`.

**Errors:** 401/403 (unauthenticated), 500

---

## Admin Authentication

To obtain an admin session:

```
POST /admin/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=<password>
```

On success, a signed session cookie is set. Pass this cookie with all subsequent admin API requests.

Unauthenticated requests to admin routes receive a 302 redirect to `/admin/login`.

---

## CSRF Tokens

State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) that originate from the browser must include the CSRF token. HTML forms embed it automatically as a hidden input via `{{ csrf_token() }}`. AJAX requests must set the `X-CSRFToken` header.

Missing or invalid CSRF token → 403.
