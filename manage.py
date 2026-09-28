"""Management CLI.

Usage:
    python manage.py init-db        # create all tables
    python manage.py seed-demo      # create an admin, employee & demo customer
    python manage.py drop-db        # drop all tables (careful!)
"""
import sys
from app import create_app
from models import db
from models.user import User, Customer, Employee
from models.account import Account

app = create_app()


def init_db():
    with app.app_context():
        db.create_all()
        print("✅ All tables created.")


def drop_db():
    with app.app_context():
        db.drop_all()
        print("⚠️  All tables dropped.")


def seed_demo():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@dsgbank.com").first():
            admin = User(full_name="System Admin", email="admin@dsgbank.com",
                         phone="9000000001", role="admin", is_verified=True)
            admin.set_password("Admin@123")
            db.session.add(admin)
            print("✅ Admin created: admin@dsgbank.com / Admin@123")

        if not User.query.filter_by(email="employee@dsgbank.com").first():
            emp_user = User(full_name="Priya Sharma", email="employee@dsgbank.com",
                             phone="9000000002", role="employee", is_verified=True)
            emp_user.set_password("Employee@123")
            db.session.add(emp_user)
            db.session.flush()
            employee = Employee(user_id=emp_user.id, employee_code="EMP001",
                                 department="Retail Banking", branch="Main Branch")
            db.session.add(employee)
            print("✅ Employee created: employee@dsgbank.com / Employee@123")

        if not User.query.filter_by(email="customer@dsgbank.com").first():
            cust_user = User(full_name="Rahul Verma", email="customer@dsgbank.com",
                              phone="9000000003", role="customer", is_verified=True)
            cust_user.set_password("Customer@123")
            db.session.add(cust_user)
            db.session.flush()
            customer = Customer(user_id=cust_user.id, kyc_status="verified")
            db.session.add(customer)
            db.session.flush()
            account = Account(customer_id=customer.id, account_type="savings", balance=50000,
                               available_balance=50000)
            db.session.add(account)
            print("✅ Demo customer created: customer@dsgbank.com / Customer@123")
            print(f"   Seeded savings account: {account.account_number} (₹50,000)")

        db.session.commit()
        print("🌱 Seed complete.")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command == "init-db":
        init_db()
    elif command == "seed-demo":
        seed_demo()
    elif command == "drop-db":
        confirm = input("Type YES to drop all tables: ")
        if confirm == "YES":
            drop_db()
    else:
        print(__doc__)
