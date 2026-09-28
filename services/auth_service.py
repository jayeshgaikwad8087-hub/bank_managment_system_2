from datetime import datetime, timedelta
from flask import current_app
from models import db
from models.security import LoginHistory


def record_login_attempt(user, success, ip_address, user_agent):
    db.session.add(LoginHistory(
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success" if success else "failed",
    ))
    if success:
        user.failed_login_attempts = 0
        user.locked_until = None
    else:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
        if user.failed_login_attempts >= max_attempts:
            lock_minutes = current_app.config.get("ACCOUNT_LOCK_MINUTES", 15)
            user.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)
    db.session.commit()
