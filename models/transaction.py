import uuid
from datetime import datetime
from models import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(36), unique=True, default=lambda: uuid.uuid4().hex.upper())

    from_account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
    to_account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)

    txn_type = db.Column(db.String(20), nullable=False)  # deposit/withdrawal/transfer/bill_payment/loan_disbursal/loan_emi
    category = db.Column(db.String(40), default="general")
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    balance_after = db.Column(db.Numeric(14, 2), nullable=True)

    status = db.Column(db.String(20), default="success")  # success/failed/pending/reversed
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    from_account = db.relationship("Account", foreign_keys=[from_account_id], back_populates="sent_transactions")
    to_account = db.relationship("Account", foreign_keys=[to_account_id], back_populates="received_transactions")


class ScheduledTransfer(db.Model):
    __tablename__ = "scheduled_transfers"

    id = db.Column(db.Integer, primary_key=True)
    from_account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey("beneficiaries.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    frequency = db.Column(db.String(20), default="monthly")  # once/weekly/monthly
    next_run_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="active")  # active/paused/completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
