import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base

db = SQLAlchemy()

def create_app():
    # Configure Flask to use the "instance/" folder for the database
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Unable to create or access instance folder {app.instance_path!r}: {e}")

    # Build the absolute path to your existing USP_Courses.db
    db_filename = "USP_Courses.db"
    full_db_path = os.path.join(app.instance_path, db_filename)

    # Use a three-slash URI for an absolute path
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{full_db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy
    db.init_app(app)
    app.db = db

    # Reflect (Automap) the existing tables in USP_Courses.db
    Base = automap_base()
    with app.app_context():
        # Reflect only; no need to call db.create_all() because the DB already exists
        Base.prepare(db.engine, reflect=True)

    # Import and register blueprints
    from routes.catalog import catalog_bp
    from routes.progress import progress_bp

    app.register_blueprint(catalog_bp, url_prefix="/catalog")
    app.register_blueprint(progress_bp, url_prefix="/progress")

    # Define a root route that redirects to /catalog
    @app.route("/")
    def index():
        return "<h2>Welcome to the USP Course Prerequisites App!<br>Go to <a href='/catalog/'>/catalog</a></h2>"

    return app

if __name__ == "__main__":
    port = int(os.getenv("PREREQ_PORT", 5007))
    create_app().run(host="0.0.0.0", port=port)
