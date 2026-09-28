from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return render_template("public/home.html")


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/services")
def services():
    return render_template("public/services.html")


@public_bp.route("/accounts/savings")
def savings_account():
    return render_template("public/savings.html")


@public_bp.route("/accounts/current")
def current_account():
    return render_template("public/current.html")


@public_bp.route("/loans-info")
def loans_info():
    return render_template("public/loans_info.html")


@public_bp.route("/cards-info")
def cards_info():
    return render_template("public/cards_info.html")


@public_bp.route("/interest-rates")
def interest_rates():
    return render_template("public/rates.html")


@public_bp.route("/security-info")
def security_info():
    return render_template("public/security_info.html")


@public_bp.route("/contact")
def contact():
    return render_template("public/contact.html")


@public_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("public/privacy.html")


@public_bp.route("/terms")
def terms():
    return render_template("public/terms.html")
