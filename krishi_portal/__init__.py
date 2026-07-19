from flask import Flask, g, session
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from krishi_portal.routes import main_bp
    from krishi_portal.models import AdminAccount, User
    from werkzeug.security import generate_password_hash

    with app.app_context():
        AdminAccount.__table__.create(bind=db.engine, checkfirst=True)
        if not db.session.scalar(db.select(AdminAccount).limit(1)):
            admin_email = app.config["ADMIN_LOGIN_EMAIL"].strip().lower()
            admin_password = app.config["ADMIN_LOGIN_PASSWORD"]
            if admin_email and admin_password:
                db.session.add(AdminAccount(
                    name="Administrator",
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                ))
                db.session.commit()

    app.register_blueprint(main_bp)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None

    @app.context_processor
    def inject_current_user():
        return {
            "current_user": g.get("user"),
            "current_admin": session.get("is_admin", False),
        }

    return app
