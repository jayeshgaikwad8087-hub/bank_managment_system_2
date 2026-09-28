from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import User, Customer
from models.transaction import Transaction
from models.support import Notification
from models.security import LoginHistory
from utils.decorators import roles_required
from utils.helpers import is_strong_password, mask_aadhaar

customer_bp = Blueprint("customer", __name__)


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@customer_bp.route("/dashboard")
@roles_required("customer")
def dashboard():
    customer = _current_customer()
    accounts = customer.accounts
    account_ids = [a.id for a in accounts]

    recent_txns = (
        Transaction.query.filter(
            (Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))
        )
        .order_by(Transaction.created_at.desc())
        .limit(8)
        .all()
    ) if account_ids else []

    income = sum(t.amount for t in recent_txns if t.to_account_id in account_ids)
    expense = sum(t.amount for t in recent_txns if t.from_account_id in account_ids)

    return render_template(
        "customer/dashboard.html",
        customer=customer,
        accounts=accounts,
        recent_txns=recent_txns,
        income=income,
        expense=expense,
        txn_count=len(recent_txns),
    )


@customer_bp.route("/profile")
@roles_required("customer")
def profile():
    customer = _current_customer()
    return render_template("customer/profile.html", customer=customer)


@customer_bp.route("/profile/edit", methods=["GET", "POST"])
@roles_required("customer")
def edit_profile():
    customer = _current_customer()
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name)
        user.phone = request.form.get("phone", user.phone)
        customer.address = request.form.get("address")
        customer.city = request.form.get("city")
        customer.state = request.form.get("state")
        customer.pincode = request.form.get("pincode")
        db.session.commit()
        session["full_name"] = user.full_name
        flash("Profile updated successfully.", "success")
        return redirect(url_for("customer.profile"))

    return render_template("customer/edit_profile.html", customer=customer, user=user)


@customer_bp.route("/kyc", methods=["GET", "POST"])
@roles_required("customer")
def kyc():
    customer = _current_customer()
    if request.method == "POST":
        customer.pan_number = request.form.get("pan_number", "").upper()
        aadhaar = request.form.get("aadhaar_number", "")
        customer.aadhaar_masked = mask_aadhaar(aadhaar)
        customer.date_of_birth = request.form.get("date_of_birth") or customer.date_of_birth
        customer.kyc_status = "pending"
        db.session.commit()
        flash("KYC documents submitted for verification.", "success")
        return redirect(url_for("customer.kyc"))
    return render_template("customer/kyc.html", customer=customer)


@customer_bp.route("/notifications")
@roles_required("customer", "employee", "admin")
def notifications():
    items = Notification.query.filter_by(user_id=session["user_id"]).order_by(
        Notification.created_at.desc()
    ).all()
    Notification.query.filter_by(user_id=session["user_id"], is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("customer/notifications.html", notifications=items)


@customer_bp.route("/security", methods=["GET", "POST"])
@roles_required("customer")
def security_settings():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
        elif new_password != confirm_password or not is_strong_password(new_password):
            flash("New password must match confirmation and meet strength rules.", "danger")
        else:
            user.set_password(new_password)
            db.session.commit()
            flash("Password changed successfully.", "success")
        return redirect(url_for("customer.security_settings"))

    login_activity = LoginHistory.query.filter_by(user_id=user.id).order_by(
        LoginHistory.created_at.desc()
    ).limit(10).all()
    return render_template("customer/security_settings.html", login_activity=login_activity)
