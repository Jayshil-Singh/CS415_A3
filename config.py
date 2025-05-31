import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    # Critical configurations that must be set
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not all([SECRET_KEY, JWT_SECRET_KEY, DATABASE_URL]):
        raise ValueError("Missing required environment variables. Please check .env file.")

    # Security configurations
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # JWT configurations
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS settings
    CORS_ORIGINS = [
        'http://127.0.0.1:5000',
        'http://127.0.0.1:5001',
        'http://127.0.0.1:5002',
        'http://127.0.0.1:5006'
    ]
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Service URLs
    SERVICES = {
        'MAIN': 'http://127.0.0.1:5000',
        'STUDENT': 'http://127.0.0.1:5001',
        'LOGIN': 'http://127.0.0.1:5002',
        'SAS': 'http://127.0.0.1:5006'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Override service URLs for production
    SERVICES = {
        'MAIN': os.environ.get('MAIN_SERVICE_URL', 'https://main.example.com'),
        'STUDENT': os.environ.get('STUDENT_SERVICE_URL', 'https://student.example.com'),
        'LOGIN': os.environ.get('LOGIN_SERVICE_URL', 'https://login.example.com'),
        'SAS': os.environ.get('SAS_SERVICE_URL', 'https://sas.example.com')
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 