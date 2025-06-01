# enrollment_services/__init__.py
from flask import Flask
from flask_migrate import Migrate
from datetime import timedelta
from .db import db # <--- IMPORTANT: Import the 'db' instance from db.py

# Initialize migrate with the db instance
migrate = Migrate()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///enrollment.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY='your_super_secret_key_here',
        JWT_EXPIRATION_DELTA=timedelta(hours=1)
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        import os
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with the app
    db.init_app(app) # <--- THIS IS THE db.init_app(app) call that needs to work
    migrate.init_app(app, db) # Pass the initialized db instance to migrate

    from .routes import enrollment_bp
    app.register_blueprint(enrollment_bp, url_prefix='/enrollment_services')

    with app.app_context():
        db.create_all()

    return app