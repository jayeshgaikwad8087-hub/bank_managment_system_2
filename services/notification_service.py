from models import db
from models.support import Notification


def notify(user_id, title, message, category="info"):
    n = Notification(user_id=user_id, title=title, message=message, category=category)
    db.session.add(n)
    db.session.commit()
    return n


def unread_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
