from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import Customer
from models.loan import Loan, calculate_emi
from models.account import Account
from services import banking_service as bank
from utils.decorators import roles_required

loan_bp = Blueprint("loan", __name__)

LOAN_RATES = {
    "personal": 12.5,
    "education": 8.5,
    "home": 8.0,
    "vehicle": 9.5,
}


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@loan_bp.route("/")
@roles_required("customer")
def loan_dashboard():
    customer = _current_customer()
    return render_template("loans/loan_dashboard.html", loans=customer.loans)


@loan_bp.route("/emi-calculator", methods=["GET", "POST"])
@roles_required("customer")
def emi_calculator():
    result = None
    if request.method == "POST":
        principal = float(request.form.get("principal", 0))
        rate = float(request.form.get("rate", 10))
        tenure = int(request.form.get("tenure", 12))
        emi = calculate_emi(principal, rate, tenure)
        total_payment = round(emi * tenure, 2)
        total_interest = round(total_payment - principal, 2)
        result = {"emi": emi, "total_payment": total_payment, "total_interest": total_interest}
    return render_template("loans/emi_calculator.html", result=result)


@loan_bp.route("/apply", methods=["GET", "POST"])
@roles_required("customer")
def apply_loan():
    customer = _current_customer()
    if request.method == "POST":
        loan_type = request.form.get("loan_type")
        principal = float(request.form.get("principal", 0))
        tenure = int(request.form.get("tenure", 12))
        purpose = request.form.get("purpose", "")

        if customer.kyc_status != "verified":
            flash("Complete KYC verification before applying for a loan.", "warning")
            return redirect(url_for("customer.kyc"))

        rate = LOAN_RATES.get(loan_type, 12.0)
        emi = calculate_emi(principal, rate, tenure)

        loan = Loan(
            customer_id=customer.id, loan_type=loan_type, principal_amount=principal,
            interest_rate=rate, tenure_months=tenure, emi_amount=emi, purpose=purpose,
        )
        db.session.add(loan)
        db.session.commit()
        flash("Loan application submitted for review.", "success")
        return redirect(url_for("loan.loan_dashboard"))

    return render_template("loans/apply_loan.html", rates=LOAN_RATES)


@loan_bp.route("/<int:loan_id>")
@roles_required("customer")
def loan_status(loan_id):
    customer = _current_customer()
    loan = Loan.query.filter_by(id=loan_id, customer_id=customer.id).first_or_404()
    return render_template("loans/loan_status.html", loan=loan)


@loan_bp.route("/<int:loan_id>/pay-emi", methods=["POST"])
@roles_required("customer")
def pay_emi(loan_id):
    customer = _current_customer()
    loan = Loan.query.filter_by(id=loan_id, customer_id=customer.id, status="active").first_or_404()
    account_id = request.form.get("account_id", type=int)
    account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
    try:
        bank.pay_loan_emi(loan, account, actor_user_id=session["user_id"])
        flash("EMI payment successful.", "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("loan.loan_status", loan_id=loan.id))
