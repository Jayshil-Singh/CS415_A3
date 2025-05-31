from flask import Flask
from app.API.config import Config
from app.Core.model import db
from app.API.routes import register_routes
import os

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance'),
        instance_relative_config=True
    )

    # Create instance directory if it doesn't exist
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # Load Configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Register routes
    register_routes(app)

    return app 