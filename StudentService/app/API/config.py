# StudentService/app/config.py

import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

class Config:
    # DB
    SQLALCHEMY_DATABASE_URI        = os.getenv('DATABASE_URL', 'sqlite:///studentservice.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # JWT
    JWT_SECRET_KEY           = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600

    DEBUG = True
