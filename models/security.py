from datetime import datetime
from models import db


class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="success")  # success/failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="login_history")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False)  # e.g. "ACCOUNT_TRANSFER", "KYC_APPROVED"
    entity_type = db.Column(db.String(40), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
