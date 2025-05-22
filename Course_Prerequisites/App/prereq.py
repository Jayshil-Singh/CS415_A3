
from flask import Blueprint, render_template

prereq_bp = Blueprint('prereq_bp', __name__, template_folder='templates', static_folder='static')

@prereq_bp.route('/')
def show_prerequisites():
    return render_template("prerequisites.html")

@prereq_bp.app_errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404

@prereq_bp.app_errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500
