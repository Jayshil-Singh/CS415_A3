# File: StudentService/app/API/config.py
import os
from dotenv import load_dotenv

# 1) Load .env from one level above "app/" (project root)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# 2) Now build an absolute path to "StudentService/instance/studentservice.db"
#      current file:   .../StudentService/app/API/config.py
#                         ↑              ↑
#                        (__file__)    we want to go two levels up to StudentService
#
db_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # .../StudentService/app/API
        '..',                        # → .../StudentService/app
        '..',                        # → .../StudentService
        'instance',
        'studentservice.db'
    )
)
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

class Config:
    # -------------------------------------------------------------
    # Database: prefer DATABASE_URL env var, otherwise sqlite:///{db_path}
    # -------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{db_path}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------
    # Flask secret key
    # ------------------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # ------------------------------
    # JWT settings
    # ------------------------------
    JWT_SECRET_KEY           = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # ------------------------------
    # Debug mode
    # ------------------------------
    DEBUG = True
