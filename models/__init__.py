from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so that they register with SQLAlchemy metadata when the
# package is imported (needed for `db.create_all()` / migrations).
from models.user import User, Customer, Employee  # noqa: E402,F401
from models.account import Account, Beneficiary  # noqa: E402,F401
from models.transaction import Transaction, ScheduledTransfer  # noqa: E402,F401
from models.card import Card, CardTransaction  # noqa: E402,F401
from models.loan import Loan, LoanPayment  # noqa: E402,F401
from models.support import Complaint, Notification  # noqa: E402,F401
from models.security import LoginHistory, AuditLog  # noqa: E402,F401
