from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import Employee, Customer, User
from models.loan import Loan
from models.transaction import Transaction
from models.security import AuditLog
from utils.decorators import roles_required
from services.notification_service import notify

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/dashboard")
@roles_required("employee")
def dashboard():
    pending_kyc = Customer.query.filter_by(kyc_status="pending").count()
    pending_loans = Loan.query.filter_by(status="pending").count()
    recent_txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    total_customers = Customer.query.count()
    return render_template(
        "employee/dashboard.html",
        pending_kyc=pending_kyc,
        pending_loans=pending_loans,
        recent_txns=recent_txns,
        total_customers=total_customers,
    )


@employee_bp.route("/customers")
@roles_required("employee")
def customer_search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        results = (
            Customer.query.join(User)
            .filter(
                (User.full_name.ilike(f"%{query}%"))
                | (User.email.ilike(f"%{query}%"))
                | (User.phone.ilike(f"%{query}%"))
            )
            .all()
        )
    return render_template("employee/customer_search.html", results=results, query=query)


@employee_bp.route("/customers/<int:customer_id>")
@roles_required("employee", "admin")
def customer_details(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template("employee/customer_details.html", customer=customer)


@employee_bp.route("/kyc-verification")
@roles_required("employee")
def kyc_verification_list():
    pending = Customer.query.filter_by(kyc_status="pending").all()
    return render_template("employee/kyc_verification.html", pending=pending)


@employee_bp.route("/kyc-verification/<int:customer_id>", methods=["POST"])
@roles_required("employee")
def review_kyc(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    decision = request.form.get("decision")
    notes = request.form.get("notes", "")
    customer.kyc_status = "verified" if decision == "approve" else "rejected"
    customer.kyc_notes = notes
    db.session.add(AuditLog(
        actor_user_id=session["user_id"], action="KYC_REVIEW", entity_type="customer",
        entity_id=customer.id, details=f"KYC {customer.kyc_status} - {notes}",
    ))
    db.session.commit()
    notify(customer.user_id, "KYC update", f"Your KYC has been {customer.kyc_status}.", "security")
    flash(f"KYC for customer #{customer.id} marked {customer.kyc_status}.", "success")
    return redirect(url_for("employee.kyc_verification_list"))


@employee_bp.route("/loan-review")
@roles_required("employee")
def loan_review_list():
    pending = Loan.query.filter_by(status="pending").order_by(Loan.applied_at.desc()).all()
    return render_template("employee/loan_review.html", pending=pending)


@employee_bp.route("/loan-review/<int:loan_id>", methods=["POST"])
@roles_required("employee")
def review_loan(loan_id):
    from datetime import datetime
    from services import banking_service as bank

    loan = Loan.query.get_or_404(loan_id)
    decision = request.form.get("decision")
    notes = request.form.get("notes", "")
    employee = Employee.query.filter_by(user_id=session["user_id"]).first()

    loan.reviewed_by = employee.id if employee else None
    loan.review_notes = notes
    loan.reviewed_at = datetime.utcnow()

    if decision == "approve":
        loan.status = "active"
        account = loan.customer.accounts[0] if loan.customer.accounts else None
        if account:
            bank.deposit(account, loan.principal_amount,
                         remarks=f"{loan.loan_type.title()} loan disbursal", actor_user_id=session["user_id"])
            loan.disbursed_account_id = account.id
    else:
        loan.status = "rejected"

    db.session.add(AuditLog(
        actor_user_id=session["user_id"], action="LOAN_REVIEW", entity_type="loan",
        entity_id=loan.id, details=f"Loan {loan.status} - {notes}",
    ))
    db.session.commit()
    notify(loan.customer.user_id, "Loan update", f"Your {loan.loan_type} loan was {loan.status}.", "loan")
    flash(f"Loan #{loan.id} marked {loan.status}.", "success")
    return redirect(url_for("employee.loan_review_list"))


@employee_bp.route("/transaction-monitoring")
@roles_required("employee", "admin")
def transaction_monitoring():
    txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(100).all()
    return render_template("employee/transaction_monitoring.html", txns=txns)
