import re
from flask import session, current_app


def currency(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return f"\u20b9{value:,.2f}"


def datetime_format(value, fmt="%d %b %Y, %I:%M %p"):
    if not value:
        return "-"
    return value.strftime(fmt)


def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        return {
            "app_name": "DSG Bank",
            "current_role": session.get("role"),
            "current_user_name": session.get("full_name"),
        }


PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=]).{8,}$"
)


def is_strong_password(password):
    """Require 8+ chars with upper, lower, digit and special character."""
    return bool(PASSWORD_PATTERN.match(password or ""))


def mask_aadhaar(aadhaar_number):
    digits = re.sub(r"\D", "", aadhaar_number or "")
    if len(digits) < 4:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{digits[-4:]}"


def client_ip(request):
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"
