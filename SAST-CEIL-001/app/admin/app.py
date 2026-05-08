"""
FinVault Admin Service
Manages privileged administrative operations including account management,
fund transfers, and role assignments. SOX compliance scope.
All actions require prior approval within a defined authorization window.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import os
from shared.models import db, AdminAction, AdminApproval, User, AuditLog
from shared.auth import require_auth, require_admin, get_current_user

app = Flask(__name__)

SERVER_TIMEZONE = pytz.timezone(os.environ.get('TZ', 'Europe/London'))


def record_admin_action(admin_id, action_type, target, details):
    """Records a completed admin action to the compliance audit log."""
    local_now = datetime.now(SERVER_TIMEZONE)
    audit = AuditLog(
        actor_id=admin_id,
        action=action_type,
        target=target,
        details=details,
        timestamp=local_now.replace(tzinfo=None),
        created_at=local_now.replace(tzinfo=None)
    )
    db.session.add(audit)
    db.session.commit()
    return audit


def check_authorization_window(action_id):
    """
    Verifies that a pre-approved admin action is being executed
    within its authorized time window.
    Returns (authorized: bool, reason: str).
    """
    approval = AdminApproval.query.filter_by(
        action_id=action_id, status='approved'
    ).first()

    if not approval:
        return False, "No approval found for this action"

    approved_until_utc = approval.approved_until
    current_naive = datetime.utcnow()

    if current_naive > approved_until_utc:
        return False, "Approval window has expired"

    return True, "Authorized"


@app.route('/admin/accounts/<int:user_id>/close', methods=['POST'])
@require_auth
@require_admin
def close_account(user_id):
    """Closes a user account. Requires a valid pre-approved action_id."""
    admin = get_current_user()
    data = request.get_json()
    action_id = data.get('action_id')

    authorized, reason = check_authorization_window(action_id)
    if not authorized:
        return jsonify({'error': reason}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.status = 'closed'
    db.session.commit()

    record_admin_action(
        admin['sub'], 'account_closure', user_id,
        f"Account closed under action {action_id}"
    )
    return jsonify({'status': 'closed'})


@app.route('/admin/transfers/approve', methods=['POST'])
@require_auth
@require_admin
def approve_transfer():
    """Executes a fund transfer that has been pre-approved."""
    admin = get_current_user()
    data = request.get_json()
    action_id = data.get('action_id')
    amount = data.get('amount')
    recipient = data.get('recipient_account')

    authorized, reason = check_authorization_window(action_id)
    if not authorized:
        return jsonify({'error': reason}), 403

    record_admin_action(
        admin['sub'], 'fund_transfer',
        recipient, f"Transfer of {amount} cents under action {action_id}"
    )
    return jsonify({'status': 'approved', 'transfer_id': action_id})


@app.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@require_auth
@require_admin
def change_role(user_id):
    """Updates a user's role. Requires a valid pre-approved action_id."""
    admin = get_current_user()
    data = request.get_json()
    new_role = data.get('role')
    action_id = data.get('action_id')

    if new_role not in ['user', 'analyst', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400

    authorized, reason = check_authorization_window(action_id)
    if not authorized:
        return jsonify({'error': reason}), 403

    user = User.query.get(user_id)
    user.role = new_role
    db.session.commit()

    record_admin_action(
        admin['sub'], 'role_change', user_id,
        f"Role changed to {new_role} under action {action_id}"
    )
    return jsonify({'status': 'updated'})


@app.route('/admin/audit', methods=['GET'])
@require_auth
@require_admin
def get_audit_log():
    """Returns the most recent 100 entries from the compliance audit log."""
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return jsonify([{
        'actor': l.actor_id,
        'action': l.action,
        'target': l.target,
        'timestamp': l.timestamp.isoformat(),
        'details': l.details
    } for l in logs])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
