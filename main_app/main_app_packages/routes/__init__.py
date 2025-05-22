from flask import Blueprint

# Import blueprints
from .audit_routes import audit_bp
from .main_routes import main_bp

# Export blueprints
__all__ = ['audit_bp', 'main_bp'] 