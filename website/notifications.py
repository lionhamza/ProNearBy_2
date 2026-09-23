# website/notifications.py
from collections import OrderedDict
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy.orm import joinedload

from . import db
from .models import User, Notification, ServiceRequest

notifications_bp = Blueprint('notifications', __name__)

# Which notification types show up under the "Requests" tab
REQUEST_TYPES = ('service_request', 'quote_request', 'request_accepted',
                 'request_declined', 'completion_requested', 'completed')


# ──────────────────────────────────────────────
#  HELPER — call this from anywhere in the app
# ──────────────────────────────────────────────
def notify(user_id, type, title, body=None, link=None, actor_id=None,
           related_type=None, related_id=None, data=None, commit=False):
    """
    Queue a notification. By default it only db.session.add()s, so it is saved
    in the SAME commit as the action that caused it (both succeed or both fail).
    Pass commit=True if you're calling it on its own.
    """
    if not user_id or user_id == actor_id:      # never notify people about their own actions
        return None
    n = Notification(user_id=int(user_id), actor_id=actor_id, type=type, title=title,
                     body=body, link=link, related_type=related_type,
                     related_id=related_id, data=data)
    db.session.add(n)
    if commit:
        db.session.commit()
    return n


# ──────────────────────────────────────────────
#  Available in EVERY template (fixes the badge only showing on some pages)
# ──────────────────────────────────────────────
@notifications_bp.app_context_processor
def inject_unread_count():
    uid = session.get('user_id')
    if not uid:
        return {'unread_notifications_count': 0}
    count = Notification.query.filter_by(user_id=uid, is_read=False).count()
    return {'unread_notifications_count': count}


@notifications_bp.app_template_filter('timeago')
def timeago(dt):
    s = int((datetime.utcnow() - dt).total_seconds())
    if s < 60:
        return 'just now'
    if s < 3600:
        return f'{s // 60} min ago'
    if s < 86400:
        return f'{s // 3600} h ago'
    if s < 7 * 86400:
        return f'{s // 86400} d ago'
    return dt.strftime('%d %b %Y')


def _group_by_day(items):
    order = ['Today', 'Yesterday', 'This week', 'Earlier']
    groups = OrderedDict((label, []) for label in order)
    today = datetime.utcnow().date()
    for n in items:
        days = (today - n.created_at.date()).days
        label = 'Today' if days <= 0 else 'Yesterday' if days == 1 else 'This week' if days < 7 else 'Earlier'
        groups[label].append(n)
    return [(label, rows) for label, rows in groups.items() if rows]


# ──────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────
@notifications_bp.route('/notifications')
def index():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('auth.login_get'))

    active_filter = request.args.get('filter', 'all')
    q = Notification.query.filter_by(user_id=uid)
    if active_filter == 'unread':
        q = q.filter_by(is_read=False)
    elif active_filter == 'requests':
        q = q.filter(Notification.type.in_(REQUEST_TYPES))

    items = (q.options(joinedload(Notification.actor))
              .order_by(Notification.created_at.desc())
              .limit(100).all())

    # Live status of any service requests referenced, so buttons always
    # reflect the current state (never stale).
    req_ids = [n.related_id for n in items if n.related_type == 'service_request' and n.related_id]
    requests_by_id = {}
    if req_ids:
        requests_by_id = {r.id: r for r in ServiceRequest.query.filter(ServiceRequest.id.in_(req_ids)).all()}

    return render_template(
        'notifications.html',
        user=User.query.get(uid),
        groups=_group_by_day(items),
        requests_by_id=requests_by_id,
        active_filter=active_filter,
        has_unread=any(not n.is_read for n in items),
    )


@notifications_bp.route('/notifications/<int:notification_id>/open')
def open(notification_id):
    """Mark as read, then go to the notification's link."""
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('auth.login_get'))
    n = Notification.query.filter_by(id=notification_id, user_id=uid).first_or_404()
    n.is_read = True
    db.session.commit()
    if n.link and n.link.startswith('/'):        # internal links only
        return redirect(n.link)
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_read(notification_id):
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('auth.login_get'))
    n = Notification.query.filter_by(id=notification_id, user_id=uid).first_or_404()
    n.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))


@notifications_bp.route('/notifications/read-all', methods=['POST'])
def mark_all_read():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('auth.login_get'))
    Notification.query.filter_by(user_id=uid, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))