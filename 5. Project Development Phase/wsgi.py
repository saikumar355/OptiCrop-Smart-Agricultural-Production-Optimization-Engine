import os
from dotenv import load_dotenv
load_dotenv()  # Load .env before any config is read

from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app

app = create_app()

# Trust one level of X-Forwarded-For / X-Forwarded-Proto from a reverse proxy
# (Nginx, AWS ALB, etc.).  Without this, rate-limiting and IP-hashing see the
# loopback address 127.0.0.1 instead of the real client IP.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_ENV', '').lower() == 'development'
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=debug_mode)
