# File: C:\Users\yashp\Documents\CS415\CS415_A3\main_app\run_main_app.py\app.py

from flask import Flask

# 1. Create the Flask application instance
# The __name__ argument helps Flask determine the root path for the application
# so that it can find resource files (like templates and static files).
# When FLASK_APP points to this file (or the module it represents),
# Flask will look for an instance named 'app' or a factory function.
app = Flask(__name__, template_folder='main_app_packages/templates', static_folder='main_app_packages/static')

# 2. Load Configurations
# It's good practice to load configurations.
# We'll assume your config.py is inside main_app_packages
# and you have a configuration class (e.g., Config, DevelopmentConfig) in it.

# Option A: If config.py has configuration variables directly
# try:
#     app.config.from_object('main_app_packages.config')
# except ImportError:
#     print("Warning: Could not import configuration from main_app_packages.config")
#     # Set some defaults if config is missing
#     app.config['SECRET_KEY'] = 'default_secret_key_in_app_py_change_me'
#     app.config['DEBUG'] = True


# Option B: If config.py has a configuration class (e.g., DevelopmentConfig)
# This is a common pattern.
# Example: from main_app_packages.config import DevelopmentConfig
# app.config.from_object(DevelopmentConfig)
# For now, let's set some basic config directly.
# **IMPORTANT**: You should move this to a config.py file for better organization.
app.config['SECRET_KEY'] = 'your_very_secret_random_key_in_app_py_CHANGE_THIS' # Change this!
app.config['DEBUG'] = True  # Set to False in production if not using a config file approach

# 3. Import and Register Blueprints or Routes
# This is crucial. After the app is created and configured, you need to
# tell Flask about your URL routes.
# Your routes are likely in main_app_packages/routes.py.
# The routes.py file will need to import 'app' from this app.py file.
# Example: from run_main_app.py.app import app (if routes.py is outside run_main_app.py)
# OR from ..app import app (if routes.py is in main_app_packages, and app.py is in run_main_app.py)

# To make this work, main_app_packages.routes will need to import 'app' from here.
# We will import it here to ensure routes are registered.
# Make sure main_app_packages.routes uses this 'app' instance.
from .main_app_packages import routes # This assumes routes.py is in main_app_packages
# and it uses the 'app' object defined in this app.py
# (which it would get via an import like 'from ..app import app')


# If you were using Blueprints defined in main_app_packages (e.g., in auth.py):
# from .main_app_packages.auth import auth_bp # Assuming auth_bp is defined in auth.py
# app.register_blueprint(auth_bp, url_prefix='/auth')


# 4. Initialize Extensions (Optional)
# If you use Flask extensions like SQLAlchemy, Flask-Login, etc.
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy(app) # Initialize directly with app
# from flask_login import LoginManager
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'main_app_packages.auth.login_route_function_name'


# 5. Optional: Add a simple test route directly in this file
@app.route('/hello_from_app_py')
def hello_from_app_py():
    return "Hello from app.py!"

# 6. Optional: Add the run block for direct execution (python app.py)
# This is useful for development if you don't want to use 'flask run'.
# However, 'flask run' is generally preferred as it uses a better development server
# and handles environment variables like FLASK_DEBUG more consistently.
if __name__ == '__main__':
    # Note: When using 'flask run', this block is NOT executed.
    # 'flask run' imports the 'app' object and runs its own development server.
    # You might need to specify host and port if running on a different machine or network.
    app.run(host='0.0.0.0', port=5000)