"""
Flask extensions are created here (without an app) so that they can be
imported anywhere in the project without causing circular imports.

They are attached to the actual Flask app inside app.py using init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Database handler.
db = SQLAlchemy()

# Authentication handler.
login_manager = LoginManager()

# Name of the route Flask-Login redirects to when login is required.
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
