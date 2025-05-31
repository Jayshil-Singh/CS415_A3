import os
from dotenv import load_dotenv
from datetime import timedelta

# Get the absolute path to the instance folder
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
instance_path = os.path.join(basedir, 'instance')

# Create instance directory if it doesn't exist
os.makedirs(instance_path, exist_ok=True)

# Database file path
db_path = os.path.join(instance_path, 'app.db')

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
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
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