from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort
)
from flask_login import login_required, current_user

from extensions import db
from models.trek import Trek
from models.user import User
from models.booking import Booking

# Routes for the admin dashboard (manage treks, staff, users, bookings).
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")



def admin_required(view):
    """Allow only logged-in admins to access the wrapped view."""
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def parse_date(value):
    """Turn a 'YYYY-MM-DD' string from the form into a date, or None."""
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()

@admin_bp.route("/admin-app")
@admin_required
def vue_admin():
    return render_template("vue_admin.html")

# ---------------------------------------------------------------------------
# Dashboard overview
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Overview page with totals, pending approvals and recent bookings."""
    stats = {
        "total_treks": Trek.query.count(),
        "total_bookings": Booking.query.count(),
        "total_users": User.query.filter_by(role="user").count(),
        "total_staff": User.query.filter_by(role="staff").count(),
    }
    pending_staff = User.query.filter_by(role="staff", approved=False).all()
    recent_bookings = (
        Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        pending_staff=pending_staff,
        recent_bookings=recent_bookings,
    )



# ---------------------------------------------------------------------------
# Trek management (CRUD + assign staff + search)
# ---------------------------------------------------------------------------
@admin_bp.route("/treks")
@admin_required
def list_treks():
    q = request.args.get("q", "").strip()
    query = Trek.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Trek.name.ilike(like),
                                    Trek.location.ilike(like)))
    treks = query.order_by(Trek.id.desc()).all()
    staff_members = User.query.filter_by(role="staff", approved=True).all()
    return render_template(
        "admin/treks.html", treks=treks, staff_members=staff_members, q=q
    )


@admin_bp.route("/treks/create", methods=["GET", "POST"])
@admin_required
def create_trek():
    staff_members = User.query.filter_by(role="staff").all()

    if request.method == "POST":
        trek = Trek(
            name=request.form.get("name", "").strip(),
            location=request.form.get("location", "").strip(),
            difficulty=request.form.get("difficulty", "").strip(),
            duration=int(request.form.get("duration") or 1),
            available_slots=int(request.form.get("available_slots") or 0),
            status=request.form.get("status", "open"),
            start_date=parse_date(request.form.get("start_date")),
            end_date=parse_date(request.form.get("end_date")),
            description=request.form.get("description", "").strip(),
            staff_id=request.form.get("staff_id") or None,
        )
        db.session.add(trek)
        db.session.commit()
        flash("Trek created successfully.", "success")
        return redirect(url_for("admin.list_treks"))

    return render_template(
        "admin/trek_form.html",
        trek=None,
        staff_members=staff_members,
        action=url_for("admin.create_trek"),
    )


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_members = User.query.filter_by(role="staff").all()

    if request.method == "POST":
        trek.name = request.form.get("name", "").strip()
        trek.location = request.form.get("location", "").strip()
        trek.difficulty = request.form.get("difficulty", "").strip()
        trek.duration = int(request.form.get("duration") or 1)
        trek.available_slots = int(request.form.get("available_slots") or 0)
        trek.status = request.form.get("status", "open")
        trek.start_date = parse_date(request.form.get("start_date"))
        trek.end_date = parse_date(request.form.get("end_date"))
        trek.description = request.form.get("description", "").strip()
        trek.staff_id = request.form.get("staff_id") or None
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.list_treks"))

    return render_template(
        "admin/trek_form.html",
        trek=trek,
        staff_members=staff_members,
        action=url_for("admin.edit_trek", trek_id=trek.id),
    )


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted.", "info")
    return redirect(url_for("admin.list_treks"))


@admin_bp.route("/treks/<int:trek_id>/assign", methods=["POST"])
@admin_required
def assign_staff(trek_id):
    """Quickly assign (or unassign) a staff member to a trek."""
    trek = Trek.query.get_or_404(trek_id)
    trek.staff_id = request.form.get("staff_id") or None
    db.session.commit()
    flash(f"Staff assignment updated for '{trek.name}'.", "success")
    return redirect(url_for("admin.list_treks"))


# ---------------------------------------------------------------------------
# User management (search + blacklist)
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
@admin_required
def list_users():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="user")
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.name.ilike(like),
                                    User.email.ilike(like)))
    users = query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users, q=q)


# ---------------------------------------------------------------------------
# Staff management (search + approve + blacklist)
# ---------------------------------------------------------------------------
@admin_bp.route("/staff")
@admin_required
def list_staff():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="staff")
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.name.ilike(like),
                                    User.email.ilike(like)))
    staff = query.order_by(User.id.desc()).all()
    return render_template("admin/staff.html", staff=staff, q=q)


@admin_bp.route("/staff/<int:user_id>/approve", methods=["POST"])
@admin_required
def approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    staff.approved = True
    db.session.commit()
    flash(f"{staff.name} has been approved.", "success")
    return redirect(url_for("admin.list_staff"))


@admin_bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@admin_required
def toggle_blacklist(user_id):
    """Blacklist or un-blacklist a user or staff account."""
    account = User.query.get_or_404(user_id)

    # Never allow an admin account to be blacklisted.
    if account.role == "admin":
        flash("Admin accounts cannot be blacklisted.", "warning")
        return redirect(url_for("admin.dashboard"))

    account.blacklisted = not account.blacklisted
    db.session.commit()

    state = "blacklisted" if account.blacklisted else "un-blacklisted"
    flash(f"{account.name} has been {state}.", "info")

    # Return to the page the account belongs to.
    if account.role == "staff":
        return redirect(url_for("admin.list_staff"))
    return redirect(url_for("admin.list_users"))


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------
@admin_bp.route("/bookings")
@admin_required
def list_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)
