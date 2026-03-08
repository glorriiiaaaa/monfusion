from flask import jsonify, session
from functools import wraps

ADMIN_USER = "ParabStore"
ADMIN_PASS = "Parab@29"


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)

    return decorated


def require_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Please login'}), 401
        return f(*args, **kwargs)

    return decorated

