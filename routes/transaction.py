from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from models.user import Customer
from models.account import Account, Beneficiary
from services import banking_service as bank
from utils.decorators import roles_required

transaction_bp = Blueprint("transaction", __name__)


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@transaction_bp.route("/deposit", methods=["GET", "POST"])
@roles_required("customer")
def deposit():
    customer = _current_customer()
    if request.method == "POST":
        account_id = request.form.get("account_id", type=int)
        amount = request.form.get("amount")
        account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
        try:
            bank.deposit(account, amount, actor_user_id=session["user_id"])
            flash(f"Deposit of ₹{amount} successful.", "success")
            return redirect(url_for("account.account_details", account_id=account.id))
        except Exception as exc:
            flash(str(exc), "danger")
    return render_template("banking/deposit.html", accounts=customer.accounts)


@transaction_bp.route("/withdraw", methods=["GET", "POST"])
@roles_required("customer")
def withdraw():
    customer = _current_customer()
    if request.method == "POST":
        account_id = request.form.get("account_id", type=int)
        amount = request.form.get("amount")
        account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
        try:
            bank.withdraw(account, amount, actor_user_id=session["user_id"])
            flash(f"Withdrawal of ₹{amount} successful.", "success")
            return redirect(url_for("account.account_details", account_id=account.id))
        except Exception as exc:
            flash(str(exc), "danger")
    return render_template("banking/withdraw.html", accounts=customer.accounts)


@transaction_bp.route("/transfer", methods=["GET", "POST"])
@roles_required("customer")
def transfer():
    customer = _current_customer()
    if request.method == "POST":
        from_account_id = request.form.get("from_account_id", type=int)
        to_identifier = request.form.get("to_account_number", "").strip()
        amount = request.form.get("amount")
        remarks = request.form.get("remarks", "Fund transfer")

        from_account = Account.query.filter_by(id=from_account_id, customer_id=customer.id).first_or_404()
        to_account = Account.query.filter_by(account_number=to_identifier).first()

        if not to_account:
            flash("Beneficiary account not found in DSG Bank.", "danger")
            return redirect(url_for("transaction.transfer"))

        try:
            debit_txn, credit_txn = bank.transfer(
                from_account, to_account, amount, remarks=remarks,
                daily_limit=current_app.config["MAX_DAILY_TRANSFER_LIMIT"],
                actor_user_id=session["user_id"],
            )
            return redirect(url_for("transaction.transfer_receipt", txn_id=debit_txn.id))
        except Exception as exc:
            flash(str(exc), "danger")

    return render_template(
        "banking/transfer.html", accounts=customer.accounts, beneficiaries=customer.beneficiaries
    )


@transaction_bp.route("/transfer/receipt/<int:txn_id>")
@roles_required("customer")
def transfer_receipt(txn_id):
    from models.transaction import Transaction
    txn = Transaction.query.get_or_404(txn_id)
    return render_template("banking/transfer_receipt.html", txn=txn)


@transaction_bp.route("/history")
@roles_required("customer")
def history():
    customer = _current_customer()
    account_ids = [a.id for a in customer.accounts]
    from models.transaction import Transaction
    txns = Transaction.query.filter(
        (Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))
    ).order_by(Transaction.created_at.desc()).all() if account_ids else []
    return render_template("customer/transactions.html", txns=txns, accounts=customer.accounts)


@transaction_bp.route("/bill-payment", methods=["GET", "POST"])
@roles_required("customer")
def bill_payment():
    customer = _current_customer()
    if request.method == "POST":
        account_id = request.form.get("account_id", type=int)
        biller = request.form.get("biller")
        amount = request.form.get("amount")
        account = Account.query.filter_by(id=account_id, customer_id=customer.id).first_or_404()
        try:
            bank.withdraw(account, amount, remarks=f"Bill payment - {biller}", actor_user_id=session["user_id"])
            flash(f"Bill payment of ₹{amount} to {biller} successful.", "success")
        except Exception as exc:
            flash(str(exc), "danger")
        return redirect(url_for("transaction.bill_payment"))
    return render_template("banking/bill_payment.html", accounts=customer.accounts)
