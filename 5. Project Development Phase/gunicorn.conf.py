"""
Gunicorn configuration for OptiCrop production deployment.

Usage:
    gunicorn --config gunicorn.conf.py wsgi:app
"""
import os

# ─── Binding ────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# ─── Workers ────────────────────────────────────────────────────────────────
# Formula: min(2 * CPU + 1, 8). Capped at 8 for predictability.
workers = min(int(os.environ.get("GUNICORN_WORKERS", "4")), 8)
worker_class = "sync"
threads = 1

# ─── Timeouts ───────────────────────────────────────────────────────────────
timeout = 120          # seconds — accommodates background retrain requests
graceful_timeout = 30
keepalive = 5

# ─── Logging ────────────────────────────────────────────────────────────────
accesslog = "-"        # stdout
errorlog  = "-"        # stderr
loglevel  = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ─── Process naming ─────────────────────────────────────────────────────────
proc_name = "opticrop"

# ─── Security ───────────────────────────────────────────────────────────────
limit_request_line   = 4096
limit_request_fields = 100
