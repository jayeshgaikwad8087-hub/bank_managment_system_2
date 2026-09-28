-- DSG Bank Management System — MySQL Schema
-- This file documents the schema for reference / manual setup.
-- In normal use, run `flask --app app init-db` (see README) to let
-- SQLAlchemy create these tables automatically from models/.

CREATE DATABASE IF NOT EXISTS dsg_bank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dsg_bank;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    public_id VARCHAR(36) UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    otp_secret VARCHAR(32),
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    date_of_birth DATE,
    address VARCHAR(255),
    city VARCHAR(80),
    state VARCHAR(80),
    pincode VARCHAR(10),
    pan_number VARCHAR(10),
    aadhaar_masked VARCHAR(20),
    kyc_status VARCHAR(20) DEFAULT 'pending',
    kyc_document_path VARCHAR(255),
    kyc_notes VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(80) DEFAULT 'Retail Banking',
    branch VARCHAR(80) DEFAULT 'Main Branch',
    designation VARCHAR(80) DEFAULT 'Relationship Manager',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL DEFAULT 'savings',
    ifsc_code VARCHAR(15) DEFAULT 'DSGB0001234',
    balance DECIMAL(14,2) DEFAULT 0,
    available_balance DECIMAL(14,2) DEFAULT 0,
    interest_rate DECIMAL(4,2) DEFAULT 3.50,
    status VARCHAR(20) DEFAULT 'active',
    daily_transfer_used DECIMAL(14,2) DEFAULT 0,
    daily_transfer_reset_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    nickname VARCHAR(80) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    ifsc_code VARCHAR(15) NOT NULL,
    bank_name VARCHAR(120) DEFAULT 'DSG Bank',
    is_internal BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_id VARCHAR(36) UNIQUE,
    from_account_id INT NULL,
    to_account_id INT NULL,
    txn_type VARCHAR(20) NOT NULL,
    category VARCHAR(40) DEFAULT 'general',
    amount DECIMAL(14,2) NOT NULL,
    balance_after DECIMAL(14,2),
    status VARCHAR(20) DEFAULT 'success',
    remarks VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_account_id) REFERENCES accounts(id),
    FOREIGN KEY (to_account_id) REFERENCES accounts(id),
    INDEX idx_txn_created_at (created_at)
);

CREATE TABLE scheduled_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_account_id INT NOT NULL,
    beneficiary_id INT NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'monthly',
    next_run_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_account_id) REFERENCES accounts(id),
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
);

CREATE TABLE cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_id INT NOT NULL,
    card_number VARCHAR(16) UNIQUE NOT NULL,
    card_type VARCHAR(20) DEFAULT 'debit',
    card_network VARCHAR(20) DEFAULT 'RuPay',
    expiry_date DATE,
    pin_hash VARCHAR(255),
    credit_limit DECIMAL(12,2) DEFAULT 0,
    outstanding_amount DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE card_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    merchant VARCHAR(120) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'success',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE TABLE loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    loan_type VARCHAR(30) NOT NULL,
    principal_amount DECIMAL(14,2) NOT NULL,
    interest_rate DECIMAL(4,2) NOT NULL,
    tenure_months INT NOT NULL,
    emi_amount DECIMAL(12,2) NOT NULL,
    purpose VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by INT NULL,
    review_notes VARCHAR(255),
    disbursed_account_id INT NULL,
    emis_paid INT DEFAULT 0,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES employees(id),
    FOREIGN KEY (disbursed_account_id) REFERENCES accounts(id)
);

CREATE TABLE loan_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    installment_number INT NOT NULL,
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
);

CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE,
    customer_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    subject VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    resolution_notes VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    message VARCHAR(255) NOT NULL,
    category VARCHAR(30) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE login_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    status VARCHAR(20) DEFAULT 'success',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    actor_user_id INT NULL,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(40),
    entity_id INT,
    details VARCHAR(255),
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_created_at (created_at),
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
);
