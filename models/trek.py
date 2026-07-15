from extensions import db


class Trek(db.Model):
    """A trekking package that users can browse and book."""

    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20), nullable=True)
    duration = db.Column(db.Integer, nullable=False, default=1)
    available_slots = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="open")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # The staff member assigned to lead this trek (optional).
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships.
    staff = db.relationship("User", backref="assigned_treks")
    bookings = db.relationship("Booking", backref="trek", lazy=True)

    def __repr__(self):
        return f"<Trek {self.name}>"
