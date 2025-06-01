
import os, functools, jwt
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Shared database object
db = SQLAlchemy()

# Use the same secret key used by login_service (.env file)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

def token_required(fn):
    """Simple JWT guard shared with other services."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({'msg': 'Missing or malformed token'}), 401
        token = auth_header.split()[1]
        try:
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'msg': 'Invalid token'}), 401
        return fn(*args, **kwargs)
    return wrapper
