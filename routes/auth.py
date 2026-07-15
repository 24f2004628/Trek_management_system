from flask import (
    Blueprint, render_template, redirect, url_for, request, flash
)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models.user import User

# All authentication routes (login, register, logout) live here.
auth_bp = Blueprint("auth", __name__)


def redirect_for_role(user):
    """Send a logged-in user to the correct landing page for their role."""
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if user.role == "staff":
        # Staff who are not approved yet see the waiting page.
        if not user.approved:
            return redirect(url_for("auth.pending"))
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("user.home"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Already logged in? No need to register again.
    if current_user.is_authenticated:
        return redirect_for_role(current_user)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        # Only 'staff' and 'user' can register; anything else becomes 'user'.
        if role not in ("staff", "user"):
            role = "user"

        # Basic validation.
        if not name or not email or not password:
            flash("Please fill in all fields.", "warning")
            return render_template("register.html")

        # Email must be unique.
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")

        # Create the account. Regular users are approved automatically;
        # staff must wait for an admin to approve them.
        user = User(
            name=name,
            email=email,
            role=role,
            approved=(role == "user"),
            blacklisted=False,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in? Go to the right dashboard.
    if current_user.is_authenticated:
        return redirect_for_role(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Wrong email or wrong password.
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        # Blacklisted accounts cannot log in.
        if user.blacklisted:
            flash("Your account has been blacklisted. Access denied.", "danger")
            return render_template("login.html")

        login_user(user)
        return redirect_for_role(user)

    return render_template("login.html")


@auth_bp.route("/pending")
@login_required
def pending():
    """Shown to staff members who are waiting for admin approval."""
    return render_template("pending.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
