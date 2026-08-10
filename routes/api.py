from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from tasks import export_booking_history
from extensions import db
from models.booking import Booking
from models.trek import Trek
from models.user import User
from redis_client import redis_client, clear_trek_cache
from tasks import export_booking_history
api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------- JSON helpers ----------

def user_json(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "approved": user.approved,
        "blacklisted": user.blacklisted,
    }


def trek_json(trek):
    return {
        "id": trek.id,
        "name": trek.name,
        "location": trek.location,
        "difficulty": trek.difficulty,
        "duration": trek.duration,
        "available_slots": trek.available_slots,
        "status": trek.status,
        "start_date": trek.start_date.isoformat() if trek.start_date else None,
        "end_date": trek.end_date.isoformat() if trek.end_date else None,
        "description": trek.description,
        "staff_id": trek.staff_id,
        "staff_name": trek.staff.name if trek.staff else None,
    }


def booking_json(booking):
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "user_name": booking.user.name,
        "user_email": booking.user.email,
        "trek_id": booking.trek_id,
        "trek_name": booking.trek.name,
        "location": booking.trek.location,
        "booking_date": booking.booking_date.isoformat(),
        "status": booking.status,
    }


# ---------- Role protection ----------

def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):

            if current_user.blacklisted:
                return {"error": "Forbidden"}, 403

            if current_user.role != role:
                return {"error": "Forbidden"}, 403

            if role == "staff" and not current_user.approved:
                return {"error": "Staff account is not approved"}, 403

            return view(*args, **kwargs)

        return wrapped

    return decorator


# ============================================================
# AUTHENTICATION
# ============================================================

@api_bp.get("/me")
def me():

    if not current_user.is_authenticated:
        return {
            "authenticated": False
        }

    return {
        "authenticated": True,
        "user": user_json(current_user)
    }


@api_bp.post("/auth/login")
def api_login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return {"error": "Invalid email or password"}, 401

    if user.blacklisted:
        return {"error": "Your account has been blacklisted"}, 403

    if user.role == "staff" and not user.approved:
        return {
            "error": "Staff account is waiting for admin approval"
        }, 403

    login_user(user)

    return {
        "message": "Login successful",
        "user": user_json(user)
    }


@api_bp.post("/auth/register")
def api_register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return {
            "error": "Name, email and password are required"
        }, 400

    if User.query.filter_by(email=email).first():
        return {
            "error": "An account with that email already exists"
        }, 409

    user = User(
        name=name,
        email=email,
        role="user",
        approved=True,
        blacklisted=False
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {
        "message": "Registration successful"
    }, 201


@api_bp.post("/auth/logout")
@login_required
def api_logout():

    logout_user()

    return {
        "message": "Logged out"
    }


# ============================================================
# USER — TREKS
# ============================================================


@api_bp.get("/treks")
def get_treks():

    q = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    duration = request.args.get("duration", "").strip()

    # Create a unique cache key based on the search filters.
    cache_key = (
        f"treks:"
        f"q={q}:"
        f"difficulty={difficulty}:"
        f"duration={duration}"
    )

    # -----------------------------------------
    # 1. Check Redis cache
    # -----------------------------------------

    cached_data = redis_client.get(cache_key)

    if cached_data:

        import json

        return json.loads(cached_data)


    # -----------------------------------------
    # 2. Cache miss → query SQLite
    # -----------------------------------------

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

        query = query.filter(
            Trek.difficulty == difficulty
        )

    if duration:

        try:

            query = query.filter(
                Trek.duration == int(duration)
            )

        except ValueError:

            return {
                "error": "Duration must be a number"
            }, 400


    treks = query.order_by(
        Trek.id.desc()
    ).all()


    result = {
        "treks": [
            trek_json(trek)
            for trek in treks
        ]
    }


    # -----------------------------------------
    # 3. Store result in Redis
    # -----------------------------------------

    import json

    redis_client.setex(
        cache_key,
        60,
        json.dumps(result)
    )


    return result


# ============================================================
# USER — BOOKING
# ============================================================

@api_bp.post("/treks/<int:trek_id>/book")
@role_required("user")
def book_trek_api(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != "open":
        return {
            "error": "This trek is not open for booking"
        }, 400

    if trek.available_slots <= 0:
        return {
            "error": "This trek is fully booked"
        }, 400

    existing = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id
    ).first()

    if existing:
        return {
            "error": "You have already booked this trek"
        }, 409

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id
    )

    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    return {
        "message": "Trek booked successfully",
        "booking": booking_json(booking)
    }, 201


@api_bp.get("/bookings")
@role_required("user")
def user_bookings():

    bookings = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return {
        "bookings": [
            booking_json(booking)
            for booking in bookings
        ]
    }


@api_bp.post("/bookings/export")
@login_required
def export_bookings():

    task = export_booking_history.delay(
        current_user.id
    )

    return {
        "message": "Booking history export started",
        "task_id": task.id
    }, 202

# ============================================================
# USER — PROFILE
# ============================================================

@api_bp.put("/profile")
@role_required("user")
def update_profile():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()

    if not name or not email:
        return {
            "error": "Name and email are required"
        }, 400

    existing = User.query.filter_by(
        email=email
    ).first()

    if existing and existing.id != current_user.id:
        return {
            "error": "That email address is already in use"
        }, 409

    current_user.name = name
    current_user.email = email

    db.session.commit()

    return {
        "message": "Profile updated",
        "user": user_json(current_user)
    }


# ============================================================
# ADMIN
# ============================================================

@api_bp.get("/admin/stats")
@role_required("admin")
def admin_stats():

    return {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(
            role="user"
        ).count(),
        "total_staff": User.query.filter_by(
            role="staff"
        ).count(),
        "total_bookings": Booking.query.count()
    }


@api_bp.post("/admin/treks")
@login_required
def create_admin_trek():

    # Only admin can create treks
    if current_user.role != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    data = request.get_json() or {}

    # Required fields
    name = data.get("name", "").strip()
    location = data.get("location", "").strip()

    if not name:
        return jsonify({
            "error": "Trek name is required"
        }), 400

    if not location:
        return jsonify({
            "error": "Location is required"
        }), 400

    # Create Trek object
    trek = Trek(
        name=name,
        location=location,
        difficulty=data.get("difficulty", "Easy"),
        duration=int(data.get("duration", 1)),
        available_slots=int(
            data.get("available_slots", 0)
        ),
        status=data.get("status", "open"),
        description=data.get("description", "")
    )

    # Dates
    from datetime import datetime

    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if start_date:
        trek.start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

    if end_date:
        trek.end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

    # Save to SQLite
    db.session.add(trek)
    db.session.commit()

    # Clear Redis cache
    clear_trek_cache()

    return jsonify({
        "message": "Trek created successfully",
        "trek": trek_json(trek)
    }), 201


@api_bp.get("/admin/users")
@role_required("admin")
def admin_users():

    q = request.args.get("q", "").strip()

    query = User.query.filter_by(
        role="user"
    )

    if q:

        like = f"%{q}%"

        query = query.filter(
            db.or_(
                User.name.ilike(like),
                User.email.ilike(like)
            )
        )

    users = query.order_by(
        User.id.desc()
    ).all()

    return {
        "users": [
            user_json(user)
            for user in users
        ]
    }


@api_bp.get("/admin/staff")
@role_required("admin")
def admin_staff():

    q = request.args.get("q", "").strip()

    query = User.query.filter_by(
        role="staff"
    )

    if q:

        like = f"%{q}%"

        query = query.filter(
            db.or_(
                User.name.ilike(like),
                User.email.ilike(like)
            )
        )

    staff = query.order_by(
        User.id.desc()
    ).all()

    return {
        "staff": [
            user_json(member)
            for member in staff
        ]
    }


@api_bp.get("/admin/bookings")
@role_required("admin")
def admin_bookings():

    bookings = (
        Booking.query
        .order_by(Booking.booking_date.desc())
        .all()
    )

    return {
        "bookings": [
            booking_json(booking)
            for booking in bookings
        ]
    }


# ============================================================
# STAFF
# ============================================================

@api_bp.get("/staff/treks")
@role_required("staff")
def staff_treks():

    treks = (
        Trek.query
        .filter_by(staff_id=current_user.id)
        .order_by(Trek.id.desc())
        .all()
    )

    result = []

    for trek in treks:

        item = trek_json(trek)

        item["participant_count"] = len(
            trek.bookings
        )

        item["participants"] = [
            booking_json(booking)
            for booking in trek.bookings
        ]

        result.append(item)

    return {
        "treks": result
    }


@api_bp.put("/staff/treks/<int:trek_id>")
@role_required("staff")
def staff_update_trek_api(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != current_user.id:
        return {
            "error": "You are not assigned to this trek"
        }, 403

    data = request.get_json(silent=True) or {}

    if "available_slots" in data:

        try:
            trek.available_slots = int(
                data["available_slots"]
            )

        except (TypeError, ValueError):

            return {
                "error": "Invalid available_slots"
            }, 400

    if "status" in data:

        trek.status = data["status"].lower()

        if trek.status in [
            "closed",
            "cancelled"
        ]:

            for booking in trek.bookings:
                booking.status = "cancelled"

        elif trek.status == "completed":

            for booking in trek.bookings:
                booking.status = "completed"

    db.session.commit()

    return {
        "trek": trek_json(trek)
    }