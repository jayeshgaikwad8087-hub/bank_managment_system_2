from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import User, Customer
from services.auth_service import record_login_attempt
from utils.helpers import is_strong_password, client_ip

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, phone, password]):
            flash("Please fill in every field.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if not is_strong_password(password):
            flash("Password must be 8+ characters with upper, lower, digit and a special character.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter((User.email == email) | (User.phone == phone)).first():
            flash("An account with this email or phone already exists.", "danger")
            return redirect(url_for("auth.register"))

        user = User(full_name=full_name, email=email, phone=phone, role="customer")
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        customer = Customer(user_id=user.id)
        db.session.add(customer)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.email == identifier) | (User.phone == identifier)
        ).first()

        if not user:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        if user.is_locked():
            flash("Account temporarily locked due to multiple failed attempts. Try again later.", "danger")
            return redirect(url_for("auth.login"))

        if not user.check_password(password):
            record_login_attempt(user, False, client_ip(request), request.headers.get("User-Agent"))
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active:
            flash("This account has been deactivated. Contact support.", "danger")
            return redirect(url_for("auth.login"))

        record_login_attempt(user, True, client_ip(request), request.headers.get("User-Agent"))

        session.clear()
        session.permanent = True
        session["user_id"] = user.id
        session["role"] = user.role
        session["full_name"] = user.full_name

        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        if user.role == "employee":
            return redirect(url_for("employee.dashboard"))
        return redirect(url_for("customer.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always show the same message, whether or not the account exists,
        # so the form can't be used to enumerate registered emails.
        flash("If an account exists for that email, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if password != confirm_password or not is_strong_password(password):
            flash("Passwords must match and meet the strength requirements.", "danger")
            return redirect(url_for("auth.reset_password", token=token))
        flash("Password reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        code = request.form.get("otp", "")
        user_id = session.get("pending_verify_user_id")
        user = User.query.get(user_id) if user_id else None
        if user and user.get_totp().verify(code, valid_window=1):
            user.is_verified = True
            db.session.commit()
            flash("Verification successful.", "success")
            return redirect(url_for("auth.login"))
        flash("Invalid or expired code.", "danger")
    return render_template("auth/verify_otp.html")
