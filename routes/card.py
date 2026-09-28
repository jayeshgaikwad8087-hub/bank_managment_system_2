from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import Customer
from models.card import Card
from models.account import Account
from utils.decorators import roles_required
from utils.helpers import is_strong_password

card_bp = Blueprint("card", __name__)


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@card_bp.route("/")
@roles_required("customer")
def my_cards():
    customer = _current_customer()
    return render_template("cards/my_cards.html", cards=customer.cards)


@card_bp.route("/request", methods=["GET", "POST"])
@roles_required("customer")
def request_card():
    customer = _current_customer()
    if request.method == "POST":
        account_id = request.form.get("account_id", type=int)
        card_type = request.form.get("card_type", "debit")
        account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
        card = Card(
            customer_id=customer.id, account_id=account.id, card_type=card_type,
            credit_limit=50000 if card_type == "credit" else 0,
        )
        db.session.add(card)
        db.session.commit()
        flash("New card issued successfully.", "success")
        return redirect(url_for("card.my_cards"))
    return render_template("cards/request_card.html", accounts=customer.accounts)


@card_bp.route("/<int:card_id>")
@roles_required("customer")
def card_details(card_id):
    customer = _current_customer()
    card = Card.query.filter_by(id=card_id, customer_id=customer.id).first_or_404()
    return render_template("cards/card_details.html", card=card)


@card_bp.route("/<int:card_id>/block", methods=["POST"])
@roles_required("customer")
def block_card(card_id):
    customer = _current_customer()
    card = Card.query.filter_by(id=card_id, customer_id=customer.id).first_or_404()
    card.status = "blocked"
    db.session.commit()
    flash("Card blocked successfully.", "info")
    return redirect(url_for("card.card_details", card_id=card.id))


@card_bp.route("/<int:card_id>/set-pin", methods=["POST"])
@roles_required("customer")
def set_pin(card_id):
    customer = _current_customer()
    card = Card.query.filter_by(id=card_id, customer_id=customer.id).first_or_404()
    pin = request.form.get("pin", "")
    if len(pin) != 4 or not pin.isdigit():
        flash("PIN must be exactly 4 digits.", "danger")
    else:
        card.set_pin(pin)
        db.session.commit()
        flash("Card PIN updated.", "success")
    return redirect(url_for("card.card_details", card_id=card.id))
