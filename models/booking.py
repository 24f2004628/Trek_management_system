from datetime import datetime

from extensions import db


class Booking(db.Model):
    """A booking made by a user for a particular trek."""

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="booked")

    # The 'user' and 'trek' relationships are provided by the backrefs
    # declared on the User and Trek models.

    def __repr__(self):
        return f"<Booking user={self.user_id} trek={self.trek_id}>"
