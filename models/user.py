import uuid
import pyotp
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class User(db.Model):
    """Base identity record. A user is exactly one of customer / employee / admin."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer/employee/admin

    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32), default=lambda: pyotp.random_base32())

    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    employee = db.relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    login_history = db.relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    # ---- Password handling ---------------------------------------------
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # ---- Account lock logic ----------------------------------------------
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > datetime.utcnow())

    def get_totp(self):
        return pyotp.TOTP(self.otp_secret)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)

    pan_number = db.Column(db.String(10), nullable=True)
    aadhaar_masked = db.Column(db.String(20), nullable=True)  # last 4 digits only, masked storage
    kyc_status = db.Column(db.String(20), default="pending")  # pending/verified/rejected
    kyc_document_path = db.Column(db.String(255), nullable=True)
    kyc_notes = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="customer")
    accounts = db.relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    beneficiaries = db.relationship("Beneficiary", back_populates="owner", cascade="all, delete-orphan")
    cards = db.relationship("Card", back_populates="customer", cascade="all, delete-orphan")
    loans = db.relationship("Loan", back_populates="customer", cascade="all, delete-orphan")
    complaints = db.relationship("Complaint", back_populates="customer", cascade="all, delete-orphan")

    def total_balance(self):
        return sum(a.balance for a in self.accounts if a.status == "active")


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(80), default="Retail Banking")
    branch = db.Column(db.String(80), default="Main Branch")
    designation = db.Column(db.String(80), default="Relationship Manager")

    user = db.relationship("User", back_populates="employee")
