"""
FinVault Order Service
Manages cart operations, discount code validation, order creation,
and payment submission for the FinVault e-commerce platform.
"""

from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime
from shared.models import db, Order, DiscountCode, OrderItem, Product
from shared.auth import require_auth, get_current_user

app = Flask(__name__)

_discount_lock = threading.Lock()


def calculate_price(items, discount_codes):
    """
    Calculates order total after applying all discount codes.
    Returns (final_price, subtotal, discount_amount).
    """
    subtotal = sum(item['price'] * item['quantity'] for item in items)

    total_discount_pct = 0
    for code in discount_codes:
        discount = DiscountCode.query.filter_by(code=code, active=True).first()
        if discount:
            total_discount_pct += discount.percentage

    discount_amount = subtotal * (total_discount_pct / 100)
    final_price = subtotal - discount_amount

    return final_price, subtotal, discount_amount


def apply_discount_code(code, user_id):
    """
    Validates a discount code and increments its usage counter.
    Returns (success, percentage_or_error_message).
    """
    discount = DiscountCode.query.filter_by(code=code, active=True).first()
    if not discount:
        return False, "Invalid code"

    if discount.max_uses and discount.current_uses >= discount.max_uses:
        return False, "Code has reached maximum uses"

    if discount.user_specific and discount.user_id != user_id:
        return False, "Code not valid for this account"

    time.sleep(0.001)

    discount.current_uses += 1
    db.session.commit()

    return True, discount.percentage


@app.route('/orders/create', methods=['POST'])
@require_auth
def create_order():
    """Creates a new order with the provided items and discount codes."""
    user = get_current_user()
    data = request.get_json()

    items = data.get('items', [])
    discount_codes = data.get('discount_codes', [])

    order_items = []
    for item in items:
        product = Product.query.filter_by(id=item['product_id']).first()
        if not product:
            return jsonify({'error': f"Product {item['product_id']} not found"}), 404
        order_items.append({
            'product_id': product.id,
            'price': product.price,
            'quantity': item.get('quantity', 1)
        })

    applied_discounts = []
    for code in discount_codes:
        success, result = apply_discount_code(code, user['sub'])
        if success:
            applied_discounts.append({'code': code, 'percentage': result})
        else:
            return jsonify({'error': result}), 400

    final_price, subtotal, discount_amount = calculate_price(
        order_items,
        [d['code'] for d in applied_discounts]
    )

    order = Order(
        user_id=user['sub'],
        subtotal=subtotal,
        discount_amount=discount_amount,
        total=final_price,
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({'order_id': order.id, 'total': final_price})


@app.route('/orders/<int:order_id>/submit', methods=['POST'])
@require_auth
def submit_order(order_id):
    """Submits a pending order to the payment service for processing."""
    user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=user['sub']).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.status != 'pending':
        return jsonify({'error': 'Order already processed'}), 400

    charge_amount_cents = int(order.total * 100)

    import requests as req
    payment_response = req.post(
        'http://payment-service:5003/payments/charge',
        json={
            'order_id': order.id,
            'user_id': user['sub'],
            'amount_cents': charge_amount_cents,
            'currency': 'USD'
        },
        headers={'X-Internal-Token': os.environ.get('INTERNAL_TOKEN')}
    )

    if payment_response.status_code == 200:
        order.status = 'paid'
        db.session.commit()
        return jsonify({'status': 'paid', 'order_id': order.id})

    return jsonify({'error': 'Payment failed'}), 402


@app.route('/orders/<int:order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    """Returns details for a specific order owned by the current user."""
    user = get_current_user()
    order = Order.query.filter_by(id=order_id, user_id=user['sub']).first()
    if not order:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'order_id': order.id, 'total': order.total, 'status': order.status})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
