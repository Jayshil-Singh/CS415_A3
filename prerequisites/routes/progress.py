from flask import Blueprint, jsonify

progress_bp = Blueprint("progress_bp", __name__)

@progress_bp.route("/")
def show_progress():
    """
    Placeholder “progress” endpoint. Returns a sample JSON structure.
    """
    sample = {
        "student_id": "s12345678",
        "completed_courses": ["CS101", "CS102"],
        "in_progress": ["CS201"],
        "remaining": ["CS301", "CS302", "CS401"]
    }
    return jsonify(sample)
