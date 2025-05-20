# StudentService/run_ss.py
from flask import Flask
# Import the function that registers your routes
from app.API.routes import register_routes

# Initialize Flask app
# The template_folder and static_folder paths are relative to where run_ss.py is located.
# Since run_ss.py is in StudentService/, and your templates/static are in StudentService/app/,
# the paths should be 'app/templates' and 'app/static'.
app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

# Register all routes and error handlers with the app instance
register_routes(app)

if __name__ == "__main__":
    # Run the app on port 5002
    app.run(debug=True, port=5002)