import uuid
from datetime import datetime
from models import db


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, default=lambda: "TCK" + uuid.uuid4().hex[:8].upper())
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    category = db.Column(db.String(50), nullable=False)  # transaction/card/loan/account/other
    subject = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="medium")  # low/medium/high
    status = db.Column(db.String(20), default="open")  # open/in_progress/resolved/closed

    resolution_notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer", back_populates="complaints")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(30), default="info")  # info/transaction/security/loan/promo
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")
