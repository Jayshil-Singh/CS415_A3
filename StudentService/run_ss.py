from flask import Flask
from app.API.config import Config     # ← this must be the file you just edited
from app.Core.models import db
from app.API.routes import register_routes

def create_app():
    app = Flask(
        __name__,
        template_folder="app/templates",
        static_folder="app/static"
    )
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()  # ← this will now create ONLY “StudentService/instance/studentservice.db”
    register_routes(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5002)
