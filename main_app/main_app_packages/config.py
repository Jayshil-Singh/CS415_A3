import os
from dotenv import load_dotenv
from datetime import timedelta

# Construct the path to the .env file located in the project root
# __file__ is 'your_project_root/main_app/main_app_package/config.py'
# os.path.dirname(__file__) is 'your_project_root/main_app/main_app_package/'
# os.path.dirname(os.path.dirname(os.path.dirname(__file__))) is 'your_project_root/'
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = True
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'  # Should match login service
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Service URLs
    PROFILE_SERVICE_URL = os.environ.get('PROFILE_SERVICE_URL') or 'http://127.0.0.1:5001'
    LOGIN_SERVICE_URL = os.environ.get('LOGIN_SERVICE_URL') or 'http://127.0.0.1:5002'
    
    # Database settings - Using SQLite for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # CORS settings
    CORS_ORIGINS = [
        'http://127.0.0.1:5000',  # Main app
        'http://127.0.0.1:5001',  # Profile service
        'http://127.0.0.1:5002',  # Login service
    ]
    
    @staticmethod
    def init_app(app):
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)