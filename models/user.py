from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    """A registered account. Role can be 'admin', 'staff' or 'user'."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    # Staff accounts must be approved by an admin before they can work.
    approved = db.Column(db.Boolean, nullable=False, default=False)

    # Blacklisted accounts are not allowed to log in.
    blacklisted = db.Column(db.Boolean, nullable=False, default=False)

    # A user can have many bookings.
    bookings = db.relationship("Booking", backref="user", lazy=True)

    def set_password(self, password):
        """Hash the given plain-text password and store it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    """Tell Flask-Login how to load a user from the session."""
    return User.query.get(int(user_id))
