import os
from dotenv import load_dotenv

# Construct the path to the .env file located in the project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///login.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't') 