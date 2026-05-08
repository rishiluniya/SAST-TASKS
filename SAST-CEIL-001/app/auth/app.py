"""
FinVault Auth Service
Handles user authentication, JWT issuance, and token validation
for all FinVault microservices.
"""

from flask import Flask, request, jsonify
import jwt
import json
import base64
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from functools import wraps
from shared.models import User, db, AuditLog

app = Flask(__name__)

RS256_PRIVATE_KEY = open('/app/keys/private.pem').read()
RS256_PUBLIC_KEY = open('/app/keys/public.pem').read()

# HMAC key used for internal service-to-service token verification
INTERNAL_SECRET = RS256_PUBLIC_KEY


def validate_token(token):
    """
    Validates a JWT token and returns the decoded payload.
    Supports both RS256 (user-facing) and HS256 (internal service) tokens.
    Returns (payload, None) on success or (None, error_message) on failure.
    """
    try:
        header = json.loads(
            base64.urlsafe_b64decode(token.split('.')[0] + '==').decode()
        )
        alg = header.get('alg', 'RS256')

        if alg == 'HS256':
            key = INTERNAL_SECRET
            verified = jwt.decode(token, key, algorithms=['HS256'])
        elif alg == 'RS256':
            verified = jwt.decode(token, RS256_PUBLIC_KEY, algorithms=['RS256'])
        else:
            return None, "Unsupported algorithm"

        return verified, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except Exception as e:
        return None, str(e)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        payload, error = validate_token(token)
        if error:
            return jsonify({'error': error}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated


@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticates a user and returns a signed JWT."""
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    from werkzeug.security import check_password_hash
    if not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401

    payload = {
        'sub': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, RS256_PRIVATE_KEY, algorithm='RS256')
    AuditLog.record('login', user.id, request.remote_addr)
    return jsonify({'token': token})


@app.route('/auth/refresh', methods=['POST'])
@require_auth
def refresh():
    """Issues a new token for an authenticated user, extending their session."""
    current = request.user
    payload = {
        'sub': current['sub'],
        'email': current['email'],
        'role': current['role'],
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    new_token = jwt.encode(payload, RS256_PRIVATE_KEY, algorithm='RS256')
    return jsonify({'token': new_token})


@app.route('/auth/validate', methods=['POST'])
def validate():
    """
    Internal endpoint for microservices to validate tokens.
    Used by order-service, payment-service, and admin-service.
    """
    token = request.get_json().get('token', '')
    payload, error = validate_token(token)
    if error:
        return jsonify({'valid': False, 'error': error}), 401
    return jsonify({'valid': True, 'payload': payload})


@app.route('/auth/public-key', methods=['GET'])
def get_public_key():
    """
    Returns the RS256 public key.
    Published for third-party integrators who need to verify
    FinVault tokens independently.
    """
    return jsonify({'public_key': RS256_PUBLIC_KEY, 'algorithm': 'RS256'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
