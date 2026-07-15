import os

from flask import Flask

from config import Config
from extensions import db, login_manager


def create_app():
    """Application factory: build and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the instance/ folder exists for the SQLite database.
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # Attach the extensions to this app.
    db.init_app(app)
    login_manager.init_app(app)

    # Import models so SQLAlchemy is aware of them before create_all().
    import models  # noqa: F401

    # Register the blueprints.
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)

    # Create the database tables (if they do not already exist) and make
    # sure the default admin account exists.
    with app.app_context():
        db.create_all()
        create_default_admin()

    return app


def create_default_admin():
    """Create the built-in admin account if it does not already exist."""
    from models.user import User

    admin = User.query.filter_by(email="admin@example.com").first()
    if admin is None:
        admin = User(
            name="Administrator",
            email="admin@example.com",
            role="admin",
            approved=True,
            blacklisted=False,
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


# Create the app at import time so "flask run" and "python app.py" both work.
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
