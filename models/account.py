import random
from datetime import datetime
from models import db


def generate_account_number():
    return "DSG" + "".join(random.choices("0123456789", k=12))


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    account_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_account_number)
    account_type = db.Column(db.String(20), nullable=False, default="savings")  # savings/current
    ifsc_code = db.Column(db.String(15), default="DSGB0001234")

    balance = db.Column(db.Numeric(14, 2), default=0)
    available_balance = db.Column(db.Numeric(14, 2), default=0)  # balance - holds
    interest_rate = db.Column(db.Numeric(4, 2), default=3.50)

    status = db.Column(db.String(20), default="active")  # active/frozen/closed
    daily_transfer_used = db.Column(db.Numeric(14, 2), default=0)
    daily_transfer_reset_date = db.Column(db.Date, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="accounts")
    sent_transactions = db.relationship(
        "Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account"
    )
    received_transactions = db.relationship(
        "Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account"
    )

    def masked_number(self):
        return "XXXX XXXX " + self.account_number[-4:]

    def reset_daily_limit_if_needed(self):
        today = datetime.utcnow().date()
        if self.daily_transfer_reset_date != today:
            self.daily_transfer_used = 0
            self.daily_transfer_reset_date = today


class Beneficiary(db.Model):
    __tablename__ = "beneficiaries"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    nickname = db.Column(db.String(80), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    ifsc_code = db.Column(db.String(15), nullable=False)
    bank_name = db.Column(db.String(120), default="DSG Bank")
    is_internal = db.Column(db.Boolean, default=False)  # internal DSG Bank account?
    status = db.Column(db.String(20), default="active")  # active/pending_verification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("Customer", back_populates="beneficiaries")
