import bcrypt
from functools import wraps
from flask import session, redirect, url_for, current_app

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_bp.admin_login_get'))
        return f(*args, **kwargs)
    return decorated_function

def verify_admin(username, password) -> bool:
    expected_username = current_app.config.get('ADMIN_USERNAME')
    expected_hash = current_app.config.get('ADMIN_PASSWORD_HASH')
    
    if not expected_username or not expected_hash:
        return False
        
    if username != expected_username:
        return False
        
    try:
        # bcrypt expects bytes for both password and hash
        return bcrypt.checkpw(password.encode('utf-8'), expected_hash.encode('utf-8'))
    except Exception:
        return False
