import os

from flask import Flask, render_template
from dotenv import load_dotenv

from config import config_by_name
from extensions import db, login_manager, migrate, csrf


def create_app(config_name=None):
    load_dotenv()

    app = Flask(__name__)

    selected = config_name or os.environ.get(
        "FLASK_CONFIG", "development"
    )

    app.config.from_object(
        config_by_name.get(selected, config_by_name["default"])
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(
        os.path.join(app.root_path, "instance"),
        exist_ok=True
    )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models
    import models

    # Import blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.classes import classes_bp
    from routes.attendance import attendance_bp
    from routes.projects import projects_bp
    from routes.submissions import submissions_bp
    from routes.messages import messages_bp

    # Register blueprints
    blueprints = [
        auth_bp,
        main_bp,
        classes_bp,
        attendance_bp,
        projects_bp,
        submissions_bp,
        messages_bp
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        return "File too large. Maximum upload size is 25 MB.", 413

    # Database initialization command
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created successfully.")

    return app


# Create Flask application
app = create_app()


if __name__ == "__main__":
    app.run()
