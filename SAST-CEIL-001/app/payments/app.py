"""
FinVault Payment Service
Processes charges, handles payment processor webhooks,
and manages refund requests. PCI DSS Level 1 scope.
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from datetime import datetime
from shared.models import db, Payment, Order, UserBalance, RefundRecord
from shared.auth import require_internal_token, require_auth, get_current_user
from shared.cache import cache

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get('PAYMENT_WEBHOOK_SECRET', '')


def verify_webhook_signature(payload, signature):
    """
    Verifies the HMAC-SHA256 signature on incoming webhook payloads.
    Compares the computed signature against the provided value.
    """
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.route('/payments/webhook', methods=['POST'])
def payment_webhook():
    """
    Receives payment status callbacks from the payment processor.
    Validates the webhook signature before processing any events.
    """
    payload = request.get_data()
    signature = request.headers.get('X-Webhook-Signature', '')

    if not verify_webhook_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.get_json()
    event_id = event.get('event_id')
    event_type = event.get('type')
    order_id = event.get('order_id')
    amount = event.get('amount_cents')

    log_webhook_event(event_id, event_type, order_id)

    if event_type == 'payment.succeeded':
        order = Order.query.get(order_id)
        if order:
            balance = UserBalance.query.filter_by(
                user_id=order.user_id
            ).first()
            if balance:
                balance.pending_credits += amount
                db.session.commit()
        return jsonify({'status': 'processed'})

    return jsonify({'status': 'ignored'})


@app.route('/payments/charge', methods=['POST'])
@require_internal_token
def charge():
    """
    Initiates a payment charge. Internal endpoint — requires
    the X-Internal-Token header issued by the order service.
    """
    data = request.get_json()
    amount_cents = data.get('amount_cents')
    order_id = data.get('order_id')
    user_id = data.get('user_id')

    payment = Payment(
        order_id=order_id,
        user_id=user_id,
        amount_cents=amount_cents,
        status='processing',
        created_at=datetime.utcnow()
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({'payment_id': payment.id, 'status': 'processing'})


@app.route('/payments/<int:payment_id>/refund', methods=['POST'])
@require_auth
def refund(payment_id):
    """Issues a refund for a completed payment owned by the current user."""
    user = get_current_user()
    payment = Payment.query.filter_by(
        id=payment_id, user_id=user['sub']
    ).first()

    if not payment:
        return jsonify({'error': 'Not found'}), 404

    cached_status = cache.get(f'payment_status_{payment_id}')
    if cached_status:
        status = cached_status
    else:
        status = payment.status
        cache.set(f'payment_status_{payment_id}', status, timeout=1)

    if status != 'succeeded':
        return jsonify({'error': f'Cannot refund payment with status: {status}'}), 400

    refund_record = RefundRecord(
        payment_id=payment_id,
        amount=payment.amount_cents,
        created_at=datetime.utcnow()
    )
    db.session.add(refund_record)
    payment.status = 'refunded'
    db.session.commit()

    import time; time.sleep(0.5)
    cache.delete(f'payment_status_{payment_id}')

    return jsonify({'refund_id': refund_record.id, 'status': 'refunded'})


def log_webhook_event(event_id, event_type, order_id):
    """Writes webhook event details to the application log."""
    print(f"Webhook: {event_id} | {event_type} | order={order_id}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
