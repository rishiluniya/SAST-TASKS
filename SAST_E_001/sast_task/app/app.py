"""
SAST-E-001 Target Application
Flask API — deliberately contains 3 true positive vulnerabilities
and 5 false positive ORM patterns for benchmark evaluation.
DO NOT deploy this in production.
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///benchmark.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Models ──────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))


# ── Routes — ORM-based (FALSE POSITIVES) ────────────────────────────────────

@app.route('/users', methods=['GET'])
def get_users():
    """Finding 1 — FALSE POSITIVE: ORM filter() call, safe"""
    username = request.args.get('username', '')
    # Semgrep flags this as potential SQL injection — it is NOT
    # SQLAlchemy parameterises this automatically
    users = User.query.filter(User.username == username).all()
    return jsonify([{'id': u.id, 'username': u.username} for u in users])


@app.route('/products', methods=['GET'])
def get_products():
    """Finding 2 — FALSE POSITIVE: ORM filter_by() call, safe"""
    name = request.args.get('name', '')
    # Semgrep flags this — it is NOT vulnerable
    # filter_by uses parameterised queries internally
    products = Product.query.filter_by(name=name).all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price} for p in products])


@app.route('/orders', methods=['GET'])
def get_orders():
    """Finding 3 — FALSE POSITIVE: ORM all() call, safe"""
    # Semgrep flags any query involving user-adjacent tables
    # Order.query.all() has no injection risk
    orders = Order.query.all()
    return jsonify([{'id': o.id, 'user_id': o.user_id} for o in orders])


@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Finding 4 — FALSE POSITIVE: ORM session.query() call, safe"""
    # Semgrep flags db.session.query patterns
    # This is standard SQLAlchemy — parameterised and safe
    user = db.session.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user.id, 'username': user.username})


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Finding 5 — FALSE POSITIVE: ORM get() call, safe"""
    # Product.query.get() fetches by primary key through ORM
    # No injection vector exists here
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': product.id, 'name': product.name})


# ── Search Endpoint — RAW QUERY (TRUE POSITIVE) ─────────────────────────────

@app.route('/search', methods=['GET'])
def search_items():
    """
    Finding 6 — TRUE POSITIVE (CWE-89): SQL Injection
    
    VULNERABLE: search_term is concatenated directly into SQL string.
    An attacker can send: search_term=' OR '1'='1
    to dump the entire items table, or worse:
    search_term='; DROP TABLE users; --
    
    This bypasses ORM because cursor.execute() is a raw DB call.
    """
    search_term = request.args.get('q', '')
    
    # VULNERABILITY: string concatenation in raw SQL
    conn = sqlite3.connect('benchmark.db')
    cursor = conn.cursor()
    query = "SELECT * FROM product WHERE name = '" + search_term + "'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return jsonify({'results': results})


# ── Config File — Hardcoded Secrets (TRUE POSITIVES) ────────────────────────
# Note: Secrets are in config.py — see that file for findings 7 and 8


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)
