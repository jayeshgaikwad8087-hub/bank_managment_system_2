from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models import db
from models.user import Customer
from models.support import Complaint
from utils.decorators import roles_required

support_bp = Blueprint("support", __name__)


def _current_customer():
    return Customer.query.filter_by(user_id=session["user_id"]).first_or_404()


@support_bp.route("/help-center")
@roles_required("customer")
def help_center():
    return render_template("support/help_center.html")


@support_bp.route("/faq")
@roles_required("customer")
def faq():
    return render_template("support/faq.html")


@support_bp.route("/complaints")
@roles_required("customer")
def complaint_history():
    customer = _current_customer()
    complaints = Complaint.query.filter_by(customer_id=customer.id).order_by(
        Complaint.created_at.desc()
    ).all()
    return render_template("support/complaint_history.html", complaints=complaints)


@support_bp.route("/complaints/new", methods=["GET", "POST"])
@roles_required("customer")
def create_complaint():
    customer = _current_customer()
    if request.method == "POST":
        complaint = Complaint(
            customer_id=customer.id,
            category=request.form.get("category", "other"),
            subject=request.form.get("subject", "").strip(),
            description=request.form.get("description", "").strip(),
            priority=request.form.get("priority", "medium"),
        )
        db.session.add(complaint)
        db.session.commit()
        flash(f"Complaint {complaint.ticket_number} submitted successfully.", "success")
        return redirect(url_for("support.complaint_history"))
    return render_template("support/create_complaint.html")


@support_bp.route("/complaints/<int:complaint_id>")
@roles_required("customer")
def complaint_details(complaint_id):
    customer = _current_customer()
    complaint = Complaint.query.filter_by(id=complaint_id, customer_id=customer.id).first_or_404()
    return render_template("support/complaint_details.html", complaint=complaint)
