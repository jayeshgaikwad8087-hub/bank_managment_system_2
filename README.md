# 🏦 DSG Bank Management System

A full-stack **Banking Management System** built with **Flask + MySQL + HTML/CSS/JS** —
role-based dashboards (Customer / Employee / Admin), a real transaction engine,
loans, cards, complaints, notifications, audit logs and a modern glassmorphism UI
with dark/light mode.

> ⚠️ **Educational / portfolio project.** This does not process real money and
> should never be used with real customer financial data.

---

## ✨ Features

- **Public site** — home, about, services, savings/current info, loan & card info, interest rates, security, contact, privacy & terms
- **Authentication** — register, login, logout, forgot/reset password, OTP verification, password strength meter, account lockout after repeated failed logins
- **Customer portal** — dashboard with live balance & analytics, profile & KYC, multiple accounts, deposit/withdraw/transfer, beneficiaries, bill payments, statements, cards, loans + EMI calculator, complaints, notifications, security settings & login activity
- **Banking transaction engine** — atomic deposit / withdraw / transfer / EMI-payment operations (classic ACID pattern — commits both ledger legs together or rolls back entirely on any failure)
- **Employee portal** — dashboard, customer search, KYC verification queue, loan review queue, transaction monitoring
- **Admin panel** — dashboard with live stats, user management, employee onboarding, KYC & loan management, transaction & complaint management, reports/analytics (Chart.js), audit logs, security monitoring
- **Security** — password hashing (Werkzeug), CSRF protection (Flask-WTF), role-based access control, session cookies (HttpOnly/SameSite), account lock after 5 failed attempts, full audit trail
- **UI/UX** — glassmorphism cards, dark/light theme toggle, toast notifications, modals, animated counters, skeleton-ready loading, responsive layout, live EMI preview

---

## 🗂️ Project Structure

```
dsg-bank/
├── app.py                 # Flask app factory + blueprint registration
├── config.py               # Environment-driven configuration
├── manage.py                # CLI: init-db / seed-demo / drop-db
├── requirements.txt
├── .env.example
├── Procfile                 # Render/Heroku-style deployment
├── database/schema.sql       # Reference MySQL schema
├── models/                   # SQLAlchemy models (users, accounts, transactions, loans, cards, ...)
├── routes/                   # Blueprints: public, auth, customer, account, transaction, loan, card, support, employee, admin
├── services/                  # banking_service (transaction engine), auth_service, notification_service
├── utils/                      # decorators (login/role guards), helpers (filters, validation)
├── static/css, static/js       # Styling & interactivity
└── templates/                  # Jinja2 templates, organized by section
```

## 🧠 Architecture

```
Browser → HTML/CSS/JS → Flask Routes → Services (business logic) → SQLAlchemy Models → MySQL
```

Every money-moving action goes through `services/banking_service.py`, which
wraps the balance updates and ledger (`Transaction`) rows in a single database
transaction — success commits everything, any exception rolls back everything.

## 🔐 Security Notes

- Passwords are salted & hashed with Werkzeug — never stored in plain text
- 5 failed login attempts locks an account for 15 minutes
- CSRF tokens are enforced on all state-changing forms via Flask-WTF
- Aadhaar numbers are stored masked (last 4 digits only); PAN and other PII are
  handled server-side only
- All admin/employee actions that touch customer data are recorded in `audit_logs`

---

## 🚀 Getting Started

### 1. Clone & install dependencies
```bash

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# edit .env with your MySQL credentials and a real SECRET_KEY
```

### 3. Create the MySQL database
```sql
CREATE DATABASE dsg_bank CHARACTER SET utf8mb4;
```
(Tables are created automatically in the next step — `database/schema.sql` is
provided purely for reference / manual setup.)

### 4. Initialize tables & seed demo data
```bash
python manage.py init-db
python manage.py seed-demo
```
This creates:
| Role     | Email                  | Password       |
|----------|------------------------|-----------------|
| Admin    | admin@dsgbank.com      | Admin@123       |
| Employee | employee@dsgbank.com   | Employee@123    |
| Customer | customer@dsgbank.com   | Customer@123    |

### 5. Run the app
```bash
python app.py
```
Visit **http://localhost:500**

---

## ☁️ Deploying to Render

1. Push this project to a GitHub repository (never commit `.env`)
2. Create a new **Web Service** on Render, connect the repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (already set in `Procfile`)
5. Add environment variables from `.env.example` in the Render dashboard,
   pointing `DATABASE_URL` / `MYSQL_*` at a managed MySQL instance
6. After the first deploy, run `python manage.py init-db` (Render Shell) to
   create tables, then `seed-demo` if you want demo logins

---

## 🎓 What This Project Demonstrates

Python · OOP · Flask routing, blueprints, sessions, templating · MySQL ·
SQLAlchemy ORM · foreign keys & relationships · ACID transactions ·
authentication & RBAC · CSRF protection · password hashing · REST-style
route design · responsive frontend (HTML/CSS/JS) · Chart.js visualization ·
Git/GitHub-ready structure · Render deployment.

## 📄 License

Educational use — adapt freely for your own portfolio or coursework.
