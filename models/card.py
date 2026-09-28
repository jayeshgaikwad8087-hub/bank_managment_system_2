import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


def generate_card_number():
    return "4" + "".join(random.choices("0123456789", k=15))


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)

    card_number = db.Column(db.String(16), unique=True, default=generate_card_number)
    card_type = db.Column(db.String(20), default="debit")  # debit/credit
    card_network = db.Column(db.String(20), default="RuPay")
    expiry_date = db.Column(db.Date, default=lambda: (datetime.utcnow() + timedelta(days=365 * 5)).date())
    pin_hash = db.Column(db.String(255), nullable=True)

    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    outstanding_amount = db.Column(db.Numeric(12, 2), default=0)

    status = db.Column(db.String(20), default="active")  # active/blocked/expired/replaced
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="cards")
    account = db.relationship("Account")
    card_transactions = db.relationship("CardTransaction", back_populates="card", cascade="all, delete-orphan")

    def masked_number(self):
        return "**** **** **** " + self.card_number[-4:]

    def set_pin(self, raw_pin):
        self.pin_hash = generate_password_hash(raw_pin)

    def check_pin(self, raw_pin):
        return self.pin_hash and check_password_hash(self.pin_hash, raw_pin)


class CardTransaction(db.Model):
    __tablename__ = "card_transactions"

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False)
    merchant = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default="success")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    card = db.relationship("Card", back_populates="card_transactions")
