"""
Application configuration.
Finding 7 — TRUE POSITIVE (CWE-798): Hardcoded API key
Finding 8 — TRUE POSITIVE (CWE-798): Hardcoded database password
"""

import os

# App settings
DEBUG = False
TESTING = False
HOST = '0.0.0.0'
PORT = 5000

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///benchmark.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Finding 7 — TRUE POSITIVE CWE-798
# Live API key hardcoded in source. Anyone with repo access has this key.
# Should be loaded from environment variable: os.environ.get('API_KEY')
API_KEY = 'sk-live-a8f3c2d19e4b7f6a2c8e1d4b9f3a7c2e'

# Finding 8 — TRUE POSITIVE CWE-798
# Production database password hardcoded in source.
# Should be loaded from environment variable: os.environ.get('DB_PASSWORD')
DB_PASSWORD = 'prod_db_p@ss2024!benchmark'

# External service endpoints
PAYMENT_SERVICE_URL = 'https://payments.internal/api/v2'
NOTIFICATION_SERVICE_URL = 'https://notify.internal/api/v1'

# Rate limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_BURST = 10
