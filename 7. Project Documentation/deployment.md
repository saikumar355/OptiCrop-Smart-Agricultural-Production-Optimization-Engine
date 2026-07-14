# Deployment Guide

This guide covers production deployment of OptiCrop with Gunicorn as the WSGI server, optionally behind an Nginx reverse proxy.

---

## Production Environment Variables Checklist

Before deploying, verify every required variable is set in your environment or `.env` file. The app halts on startup if any required variable is absent.

### Required

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask session secret — long random string | `openssl rand -hex 32` |
| `CSRF_SECRET_KEY` | CSRF protection secret — separate from `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_USERNAME` | Admin dashboard login username | `admin` |
| `ADMIN_PASSWORD_HASH` | bcrypt hash of the admin password | `$2b$12$...` |
| `ACTIVE_MODEL_PATH` | Path to the active model `.pkl` artifact | `saved_models/ExtraTrees_2026-07-01T122126Z.pkl` |
| `ACTIVE_SCALER_PATH` | Path to the active scaler `.pkl` artifact | `saved_models/scaler_2026-07-01T122126Z.pkl` |
| `DATASET_PATH` | Path to the training CSV | `datasets/crop_recommendation.csv` |
| `SUITABILITY_THRESHOLDS` | JSON string of per-crop agronomic thresholds | `'{...}'` |

### Recommended to Change from Defaults

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_PATH` | `instance/opticrop.db` | Use an absolute path on a persistent volume |
| `LOG_PATH` | `logs/opticrop.log` | Use an absolute path; ensure the directory exists |
| `FLASK_ENV` | `production` | Always `production` in live environments |
| `RATELIMIT_STORAGE_URL` | `memory://` | Use Redis (`redis://localhost:6379`) for multi-worker deployments |
| `GUNICORN_WORKERS` | `4` | See worker tuning below |

### Security Notes

- Never commit `.env` to version control (`.gitignore` already excludes it).
- Rotate `SECRET_KEY` and `CSRF_SECRET_KEY` if they are ever exposed.
- `ADMIN_PASSWORD_HASH` must be a bcrypt hash, never a plaintext password.

---

## Gunicorn Worker Count Tuning

The recommended formula for synchronous workers:

```
workers = min(2 * CPU_count + 1, 8)
```

| CPUs | Workers (formula) | Capped at |
|---|---|---|
| 1 | 3 | 3 |
| 2 | 5 | 5 |
| 4 | 9 | **8** |
| 8 | 17 | **8** |

Set in `.env`:
```ini
GUNICORN_WORKERS=5
```

The `gunicorn.conf.py` reads this value and hard-caps it at 8:
```python
workers = min(int(os.environ.get("GUNICORN_WORKERS", "4")), 8)
```

Additional Gunicorn settings:
```ini
timeout = 120       # seconds — increase if training requests take longer
loglevel = info     # info | warning | error
```

Start Gunicorn manually:
```bash
gunicorn --config gunicorn.conf.py wsgi:app
```

---

## Log Rotation

OptiCrop writes structured logs to `logs/opticrop.log`. Configure `logrotate` to prevent unbounded growth.

Create `/etc/logrotate.d/opticrop`:

```
/path/to/opticrop/logs/opticrop.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

`copytruncate` truncates the live log file rather than moving it, so Gunicorn does not need a restart after rotation.

Test the config:
```bash
logrotate --debug /etc/logrotate.d/opticrop
```

---

## Nginx Reverse Proxy

Running OptiCrop behind Nginx provides TLS termination, connection buffering, and static file serving.

### Nginx Site Configuration

```nginx
server {
    listen 80;
    server_name example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    # Serve static files directly (optional — skips Gunicorn for assets)
    location /static/ {
        alias /path/to/opticrop/app/static/;
        expires 30d;
        access_log off;
    }

    # Proxy everything else to Gunicorn
    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

Reload Nginx after editing:
```bash
nginx -t && systemctl reload nginx
```

### Flask `ProxyFix` Middleware

When behind Nginx, Flask must be told to trust the `X-Forwarded-For` header so rate limiting and IP hashing see the real client IP. Add to `wsgi.py` or `create_app()`:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```

---

## Health Check Endpoint

`GET /api/health` returns HTTP 200 as long as the process is running:

```json
{"status": "ok", "uptime_seconds": 3600}
```

Use it for:

- **Docker healthcheck** — configured in both `Dockerfile` and `docker-compose.yml`.
- **Load balancer liveness probes** — point the probe at `/api/health`.
- **Uptime monitoring** — alert if this endpoint stops returning 200.

The endpoint returns 200 even if no model is loaded (the app logs a warning but remains available for non-prediction routes).

---

## Systemd Service (Optional)

To run OptiCrop as a systemd service on Linux:

```ini
# /etc/systemd/system/opticrop.service
[Unit]
Description=OptiCrop Gunicorn Service
After=network.target

[Service]
User=opticrop
Group=opticrop
WorkingDirectory=/path/to/opticrop
EnvironmentFile=/path/to/opticrop/.env
ExecStart=/path/to/opticrop/.venv/bin/gunicorn \
    --config gunicorn.conf.py \
    --bind 127.0.0.1:5000 \
    wsgi:app
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable opticrop
systemctl start opticrop
systemctl status opticrop
```
