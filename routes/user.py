from flask import (
    Blueprint, abort, render_template, redirect, url_for, flash, request
)
from flask_login import login_required, current_user

from extensions import db
from models.trek import Trek
from models.booking import Booking
from models.user import User
# Routes for regular users (browse treks, make bookings).
user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def home():
    q = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    duration = request.args.get("duration", "").strip()

    query = Trek.query.filter_by(status="open")

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Trek.name.ilike(like),
                Trek.location.ilike(like)
            )
        )

    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)

    if duration:
        query = query.filter(Trek.duration == int(duration))

    treks = query.order_by(Trek.id.desc()).all()

    return render_template(
        "user/treks.html",
        treks=treks,
        q=q,
        difficulty=difficulty,
        duration=duration
    )


@user_bp.route("/dashboard")
@login_required
def dashboard():
    """Show the treks the current user has booked."""
    bookings = (
    Booking.query.filter_by(
        user_id=current_user.id,
        status="booked"
    )
    .order_by(Booking.booking_date.desc())
    .all()
)
    return render_template("user/dashboard.html", bookings=bookings)
@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            flash("Name and email are required.", "warning")
            return render_template("user/profile.html")

        # Check whether another account already uses this email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user and existing_user.id != current_user.id:
            flash("That email address is already in use.", "danger")
            return render_template("user/profile.html")

        current_user.name = name
        current_user.email = email

        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html")
@user_bp.route("/history")
@login_required
def history():
    bookings = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return render_template(
        "user/history.html",
        bookings=bookings
    )
@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@login_required

def book_trek(trek_id):
    if current_user.role != "user":
        abort(403)
    trek = Trek.query.get_or_404(trek_id)

    # Rule: the trek must be open for booking.
    if trek.status != "open":
        flash("This trek is not open for booking.", "warning")
        return redirect(url_for("user.home"))

    # Rule: there must be at least one slot available.
    if trek.available_slots <= 0:
        flash("Sorry, this trek is fully booked.", "warning")
        return redirect(url_for("user.home"))

    # Rule: a user cannot book the same trek twice.
    existing = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id
    ).first()
    if existing:
        flash("You have already booked this trek.", "info")
        return redirect(url_for("user.dashboard"))

    # Create the booking and reduce the available slots.
    booking = Booking(user_id=current_user.id, trek_id=trek.id)
    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    flash(f"You have successfully booked '{trek.name}'.", "success")
    return redirect(url_for("user.dashboard"))
