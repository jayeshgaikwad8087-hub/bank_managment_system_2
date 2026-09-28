"""Core transaction engine.

Every money-movement operation goes through here so that balance changes and
their corresponding ledger (Transaction) rows are always written atomically:
either both succeed and are committed together, or neither is applied.
"""
from decimal import Decimal
from datetime import datetime

from models import db
from models.transaction import Transaction
from models.security import AuditLog
from services.notification_service import notify


class InsufficientFundsError(Exception):
    pass


class TransferLimitExceeded(Exception):
    pass


class InvalidAmountError(Exception):
    pass


def _validate_amount(amount):
    try:
        amount = Decimal(str(amount))
    except Exception:
        raise InvalidAmountError("Amount must be a valid number.")
    if amount <= 0:
        raise InvalidAmountError("Amount must be greater than zero.")
    return amount


def deposit(account, amount, remarks="Cash deposit", actor_user_id=None):
    amount = _validate_amount(amount)
    try:
        account.balance = account.balance + amount
        account.available_balance = account.balance
        txn = Transaction(
            to_account_id=account.id,
            txn_type="deposit",
            category="deposit",
            amount=amount,
            balance_after=account.balance,
            remarks=remarks,
        )
        db.session.add(txn)
        db.session.add(AuditLog(actor_user_id=actor_user_id, action="DEPOSIT",
                                 entity_type="account", entity_id=account.id,
                                 details=f"Deposited {amount} to {account.account_number}"))
        db.session.commit()
        notify(account.customer.user_id, "Deposit received",
               f"₹{amount} was credited to account {account.masked_number()}.", "transaction")
        return txn
    except Exception:
        db.session.rollback()
        raise


def withdraw(account, amount, remarks="Cash withdrawal", actor_user_id=None):
    amount = _validate_amount(amount)
    if account.available_balance < amount:
        raise InsufficientFundsError("Insufficient balance for this withdrawal.")
    try:
        account.balance = account.balance - amount
        account.available_balance = account.balance
        txn = Transaction(
            from_account_id=account.id,
            txn_type="withdrawal",
            category="withdrawal",
            amount=amount,
            balance_after=account.balance,
            remarks=remarks,
        )
        db.session.add(txn)
        db.session.add(AuditLog(actor_user_id=actor_user_id, action="WITHDRAWAL",
                                 entity_type="account", entity_id=account.id,
                                 details=f"Withdrew {amount} from {account.account_number}"))
        db.session.commit()
        notify(account.customer.user_id, "Withdrawal successful",
               f"₹{amount} was debited from account {account.masked_number()}.", "transaction")
        return txn
    except Exception:
        db.session.rollback()
        raise


def transfer(from_account, to_account, amount, remarks="Fund transfer",
             daily_limit=None, actor_user_id=None):
    """Atomic transfer between two accounts (can be same-bank internal transfer).

    Demonstrates the classic banking ACID pattern: debit + credit + two ledger
    rows are all written inside one database transaction. If anything fails,
    the whole operation rolls back and no partial state is persisted.
    """
    amount = _validate_amount(amount)

    if from_account.id == to_account.id:
        raise InvalidAmountError("Cannot transfer to the same account.")

    from_account.reset_daily_limit_if_needed()

    if from_account.available_balance < amount:
        raise InsufficientFundsError("Insufficient balance for this transfer.")

    if daily_limit is not None:
        if from_account.daily_transfer_used + amount > Decimal(str(daily_limit)):
            raise TransferLimitExceeded("This transfer exceeds your daily transfer limit.")

    try:
        # Debit sender
        from_account.balance -= amount
        from_account.available_balance = from_account.balance
        from_account.daily_transfer_used += amount

        # Credit receiver
        to_account.balance += amount
        to_account.available_balance = to_account.balance

        debit_txn = Transaction(
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            txn_type="transfer",
            category="transfer_debit",
            amount=amount,
            balance_after=from_account.balance,
            remarks=remarks,
        )
        credit_txn = Transaction(
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            txn_type="transfer",
            category="transfer_credit",
            amount=amount,
            balance_after=to_account.balance,
            remarks=remarks,
        )
        db.session.add_all([debit_txn, credit_txn])
        db.session.add(AuditLog(
            actor_user_id=actor_user_id, action="FUND_TRANSFER", entity_type="account",
            entity_id=from_account.id,
            details=f"Transferred {amount} from {from_account.account_number} to {to_account.account_number}",
        ))
        db.session.commit()

        notify(from_account.customer.user_id, "Money sent",
               f"₹{amount} sent to account ending {to_account.account_number[-4:]}.", "transaction")
        notify(to_account.customer.user_id, "Money received",
               f"₹{amount} credited from account ending {from_account.account_number[-4:]}.", "transaction")
        return debit_txn, credit_txn
    except Exception:
        db.session.rollback()
        raise


def pay_loan_emi(loan, from_account, actor_user_id=None):
    from models.loan import LoanPayment

    amount = Decimal(str(loan.emi_amount))
    if from_account.available_balance < amount:
        raise InsufficientFundsError("Insufficient balance to pay this EMI.")
    try:
        from_account.balance -= amount
        from_account.available_balance = from_account.balance
        loan.emis_paid += 1

        payment = LoanPayment(loan_id=loan.id, amount=amount, installment_number=loan.emis_paid)
        txn = Transaction(
            from_account_id=from_account.id,
            txn_type="loan_emi",
            category="loan_emi",
            amount=amount,
            balance_after=from_account.balance,
            remarks=f"EMI #{loan.emis_paid} for loan {loan.id}",
        )
        db.session.add_all([payment, txn])
        if loan.emis_paid >= loan.tenure_months:
            loan.status = "closed"
        db.session.add(AuditLog(actor_user_id=actor_user_id, action="LOAN_EMI_PAID",
                                 entity_type="loan", entity_id=loan.id,
                                 details=f"EMI #{loan.emis_paid} of {amount} paid"))
        db.session.commit()
        notify(from_account.customer.user_id, "EMI paid",
               f"EMI of ₹{amount} paid for your {loan.loan_type} loan.", "loan")
        return txn
    except Exception:
        db.session.rollback()
        raise
