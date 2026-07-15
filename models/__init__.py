"""
Import the models here so that a single import of the models package makes
every model known to SQLAlchemy (needed for db.create_all()).
"""

from models.user import User
from models.trek import Trek
from models.booking import Booking
