# enrollment_services/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
# No create_app function here anymore
# No app.config.from_object(...) here