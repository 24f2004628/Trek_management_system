from functools import wraps
from models import trek
from models.booking import Booking
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort
)
from flask_login import login_required, current_user

from extensions import db
from models.trek import Trek

# Routes for staff members (manage assigned treks and bookings).
staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


def approved_staff_required(view):
    """Allow only logged-in, approved staff to access the wrapped view."""
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "staff":
            abort(403)
        # Unapproved staff are sent to the waiting page instead.
        if not current_user.approved:
            return redirect(url_for("auth.pending"))
        return view(*args, **kwargs)
    return wrapped


@staff_bp.route("/dashboard")
@approved_staff_required
def dashboard():
    """Show the treks assigned to this staff member and their participants."""
    treks = Trek.query.filter_by(staff_id=current_user.id).all()
    return render_template("staff/dashboard.html", treks=treks)

@staff_bp.route("/treks/<int:trek_id>/participants")
@approved_staff_required
def participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # Only assigned staff can view participants
    if trek.staff_id != current_user.id:
        abort(403)

    bookings = Booking.query.filter_by(trek_id=trek.id).all()

    return render_template(
        "staff/participants.html",
        trek=trek,
        bookings=bookings
    )

@staff_bp.route("/staff-app")
@approved_staff_required
def vue_staff():
    return render_template("vue_staff.html")



@staff_bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@approved_staff_required
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    

    # Only the assigned staff member may edit this trek.
    if trek.staff_id != current_user.id:
        abort(403)

    trek.available_slots = int(request.form.get("available_slots") or 0)
    trek.status = request.form.get("status", trek.status)
    bookings = Booking.query.filter_by(trek_id=trek.id).all()

    if trek.status.lower() in ["cancelled", "closed"]:
        for booking in bookings:
            booking.status = "cancelled"

    elif trek.status.lower() == "completed":
        for booking in bookings:
            booking.status = "completed"



    db.session.commit()

    flash(f"'{trek.name}' updated successfully.", "success")
    return redirect(url_for("staff.dashboard"))