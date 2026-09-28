from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import User, Customer, Employee
from models.account import Account
from models.transaction import Transaction
from models.loan import Loan
from models.card import Card
from models.support import Complaint
from models.security import AuditLog
from utils.decorators import roles_required
from utils.helpers import is_strong_password

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@roles_required("admin")
def dashboard():
    stats = {
        "total_customers": Customer.query.count(),
        "total_accounts": Account.query.count(),
        "total_deposits": db.session.query(db.func.coalesce(db.func.sum(Account.balance), 0)).scalar(),
        "total_transactions": Transaction.query.count(),
        "active_loans": Loan.query.filter_by(status="active").count(),
        "pending_loans": Loan.query.filter_by(status="pending").count(),
        "open_complaints": Complaint.query.filter(Complaint.status.in_(["open", "in_progress"])).count(),
        "total_cards": Card.query.count(),
    }
    recent_audit = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_audit=recent_audit)


@admin_bp.route("/users")
@roles_required("admin")
def user_management():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/user_management.html", users=users)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@roles_required("admin")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.add(AuditLog(
        actor_user_id=session["user_id"], action="USER_STATUS_TOGGLE", entity_type="user",
        entity_id=user.id, details=f"is_active set to {user.is_active}",
    ))
    db.session.commit()
    flash(f"User {user.email} is now {'active' if user.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.user_management"))


@admin_bp.route("/employees/new", methods=["GET", "POST"])
@roles_required("admin")
def create_employee():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email", "").lower()
        phone = request.form.get("phone")
        password = request.form.get("password")
        employee_code = request.form.get("employee_code")
        department = request.form.get("department", "Retail Banking")
        branch = request.form.get("branch", "Main Branch")

        if User.query.filter((User.email == email) | (User.phone == phone)).first():
            flash("A user with this email or phone already exists.", "danger")
            return redirect(url_for("admin.create_employee"))

        user = User(full_name=full_name, email=email, phone=phone, role="employee", is_verified=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        employee = Employee(user_id=user.id, employee_code=employee_code, department=department, branch=branch)
        db.session.add(employee)
        db.session.commit()
        flash(f"Employee account created for {full_name}.", "success")
        return redirect(url_for("admin.user_management"))

    return render_template("admin/create_employee.html")


@admin_bp.route("/kyc-management")
@roles_required("admin")
def kyc_management():
    customers = Customer.query.order_by(Customer.kyc_status).all()
    return render_template("admin/kyc_management.html", customers=customers)


@admin_bp.route("/loan-management")
@roles_required("admin")
def loan_management():
    loans = Loan.query.order_by(Loan.applied_at.desc()).all()
    return render_template("admin/loan_management.html", loans=loans)


@admin_bp.route("/transaction-management")
@roles_required("admin")
def transaction_management():
    txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(200).all()
    return render_template("admin/transaction_management.html", txns=txns)


@admin_bp.route("/complaints")
@roles_required("admin")
def complaint_management():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template("admin/complaint_management.html", complaints=complaints)


@admin_bp.route("/complaints/<int:complaint_id>/resolve", methods=["POST"])
@roles_required("admin")
def resolve_complaint(complaint_id):
    from datetime import datetime
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = "resolved"
    complaint.resolution_notes = request.form.get("resolution_notes", "")
    complaint.resolved_at = datetime.utcnow()
    db.session.commit()
    flash(f"Complaint {complaint.ticket_number} resolved.", "success")
    return redirect(url_for("admin.complaint_management"))


@admin_bp.route("/reports")
@roles_required("admin")
def reports():
    from collections import OrderedDict
    from decimal import Decimal

    # Aggregated in Python rather than with a DB-specific date function
    # (e.g. MySQL's DATE_FORMAT), so this works the same on any backend.
    totals = OrderedDict()
    txns = Transaction.query.order_by(Transaction.created_at.asc()).all()
    for txn in txns:
        month_key = txn.created_at.strftime("%Y-%m")
        totals[month_key] = totals.get(month_key, Decimal("0")) + txn.amount

    monthly = [{"month": k, "total": float(v)} for k, v in list(totals.items())[-12:]]
    return render_template("admin/reports.html", monthly=monthly)


@admin_bp.route("/audit-logs")
@roles_required("admin")
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("admin/audit_logs.html", logs=logs)


@admin_bp.route("/security-monitoring")
@roles_required("admin")
def security_monitoring():
    from models.security import LoginHistory
    failed_logins = LoginHistory.query.filter_by(status="failed").order_by(
        LoginHistory.created_at.desc()
    ).limit(100).all()
    locked_users = User.query.filter(User.locked_until.isnot(None)).all()
    return render_template("admin/security_monitoring.html", failed_logins=failed_logins, locked_users=locked_users)
