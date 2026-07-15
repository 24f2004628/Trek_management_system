import os

# Absolute path to the folder that contains this file (the project root).
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration for the Trekking Management application."""

    # Used by Flask to secure sessions and Flask-Login cookies.
    SECRET_KEY = os.environ.get("SECRET_KEY", "DanishUllahKhan")

    # SQLite database stored inside the instance/ folder.
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        BASE_DIR, "instance", "trek.db"
    )

    # Disable a feature we do not need; also silences a warning.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
