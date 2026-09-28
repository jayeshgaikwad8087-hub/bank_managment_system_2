from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped


def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
