import os
from flask import Flask, render_template
from flask_wtf import CSRFProtect

from config import config_map
from models import db
from utils.helpers import currency, datetime_format, register_context_processors


csrf = CSRFProtect()


def create_app(env_name=None):
    app = Flask(__name__)
    env_name = env_name or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config_map.get(env_name, config_map["default"]))

    db.init_app(app)
    csrf.init_app(app)

    # Jinja filters
    app.jinja_env.filters["currency"] = currency
    app.jinja_env.filters["dtfmt"] = datetime_format
    register_context_processors(app)

    # ---- Blueprints -----------------------------------------------------
    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.account import account_bp
    from routes.transaction import transaction_bp
    from routes.loan import loan_bp
    from routes.card import card_bp
    from routes.support import support_bp
    from routes.employee import employee_bp
    from routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(customer_bp, url_prefix="/customer")
    app.register_blueprint(account_bp, url_prefix="/customer/accounts")
    app.register_blueprint(transaction_bp, url_prefix="/customer/banking")
    app.register_blueprint(loan_bp, url_prefix="/customer/loans")
    app.register_blueprint(card_bp, url_prefix="/customer/cards")
    app.register_blueprint(support_bp, url_prefix="/customer/support")
    app.register_blueprint(employee_bp, url_prefix="/employee")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.after_request
    def set_secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
