# StudentService/run_ss.py

from flask import Flask
from app.API.config import Config
from app.Core.model import db
from app.API.routes import register_routes

# --- Initialize Flask app ---
# Since run_ss.py lives in StudentService/,
# and your templates/static live in StudentService/app/,
# we point at app/templates and app/static:
app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

# --- Load Configuration ---
app.config.from_object(Config)

# --- Initialize and create your database tables ---
db.init_app(app)
with app.app_context():
    db.create_all()

# --- Register all of your routes (including auth_bp/login) ---
register_routes(app)

# --- Run the server ---
if __name__ == "__main__":
    app.run(debug=True, port=5002)
