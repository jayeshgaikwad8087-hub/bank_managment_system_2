from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import Customer
from models.account import Account, Beneficiary
from models.transaction import Transaction
from utils.decorators import roles_required

account_bp = Blueprint("account", __name__)


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@account_bp.route("/")
@roles_required("customer")
def list_accounts():
    customer = _current_customer()
    return render_template("customer/accounts.html", accounts=customer.accounts, customer=customer)


@account_bp.route("/new", methods=["GET", "POST"])
@roles_required("customer")
def open_account():
    customer = _current_customer()
    if request.method == "POST":
        account_type = request.form.get("account_type", "savings")
        rate = 3.50 if account_type == "savings" else 0.0
        account = Account(customer_id=customer.id, account_type=account_type, interest_rate=rate)
        db.session.add(account)
        db.session.commit()
        flash(f"New {account_type} account {account.account_number} opened.", "success")
        return redirect(url_for("account.list_accounts"))
    return render_template("customer/open_account.html")


@account_bp.route("/<int:account_id>")
@roles_required("customer")
def account_details(account_id):
    customer = _current_customer()
    account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
    txns = Transaction.query.filter(
        (Transaction.from_account_id == account.id) | (Transaction.to_account_id == account.id)
    ).order_by(Transaction.created_at.desc()).limit(20).all()
    return render_template("customer/account_details.html", account=account, txns=txns)


@account_bp.route("/<int:account_id>/statement")
@roles_required("customer")
def statement(account_id):
    customer = _current_customer()
    account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
    txns = Transaction.query.filter(
        (Transaction.from_account_id == account.id) | (Transaction.to_account_id == account.id)
    ).order_by(Transaction.created_at.desc()).all()
    return render_template("customer/statement.html", account=account, txns=txns)


@account_bp.route("/beneficiaries")
@roles_required("customer")
def beneficiaries():
    customer = _current_customer()
    return render_template("customer/beneficiaries.html", beneficiaries=customer.beneficiaries)


@account_bp.route("/beneficiaries/add", methods=["GET", "POST"])
@roles_required("customer")
def add_beneficiary():
    customer = _current_customer()
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        account_number = request.form.get("account_number", "").strip()
        ifsc_code = request.form.get("ifsc_code", "").strip().upper()
        bank_name = request.form.get("bank_name", "DSG Bank").strip()

        if not all([nickname, account_number, ifsc_code]):
            flash("Please fill in every field.", "danger")
            return redirect(url_for("account.add_beneficiary"))

        is_internal = Account.query.filter_by(account_number=account_number).first() is not None
        beneficiary = Beneficiary(
            customer_id=customer.id,
            nickname=nickname,
            account_number=account_number,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            is_internal=is_internal,
            status="active",
        )
        db.session.add(beneficiary)
        db.session.commit()
        flash("Beneficiary added successfully.", "success")
        return redirect(url_for("account.beneficiaries"))
    return render_template("customer/add_beneficiary.html")


@account_bp.route("/beneficiaries/<int:beneficiary_id>/delete", methods=["POST"])
@roles_required("customer")
def delete_beneficiary(beneficiary_id):
    customer = _current_customer()
    beneficiary = Beneficiary.query.filter_by(id=beneficiary_id, customer_id=customer.id).first_or_404()
    db.session.delete(beneficiary)
    db.session.commit()
    flash("Beneficiary removed.", "info")
    return redirect(url_for("account.beneficiaries"))
