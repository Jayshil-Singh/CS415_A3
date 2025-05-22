from flask import Blueprint, render_template

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def homepage():
    return render_template('homepage.html')
