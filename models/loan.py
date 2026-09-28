from datetime import datetime
from models import db


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    loan_type = db.Column(db.String(30), nullable=False)  # personal/education/home/vehicle
    principal_amount = db.Column(db.Numeric(14, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(4, 2), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    emi_amount = db.Column(db.Numeric(12, 2), nullable=False)

    purpose = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected/active/closed
    reviewed_by = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)
    review_notes = db.Column(db.String(255), nullable=True)

    disbursed_account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
    emis_paid = db.Column(db.Integer, default=0)

    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer", back_populates="loans")
    payments = db.relationship("LoanPayment", back_populates="loan", cascade="all, delete-orphan")

    def outstanding_balance(self):
        total_payable = self.emi_amount * self.tenure_months
        paid = self.emi_amount * self.emis_paid
        return max(total_payable - paid, 0)


class LoanPayment(db.Model):
    __tablename__ = "loan_payments"

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    loan = db.relationship("Loan", back_populates="payments")


def calculate_emi(principal, annual_rate, tenure_months):
    """Standard reducing-balance EMI formula."""
    monthly_rate = (float(annual_rate) / 12) / 100
    principal = float(principal)
    if monthly_rate == 0:
        return round(principal / tenure_months, 2)
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return round(emi, 2)
