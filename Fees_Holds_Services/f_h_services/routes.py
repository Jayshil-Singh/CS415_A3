from flask import Blueprint, render_template

fnh_bp = Blueprint('fnh', __name__)

@fnh_bp.route('/fees')
def fees():
    # Dummy data for demonstration purposes
    total_fees = 1850.00
    holds = []  # Empty list for no holds
    fee_status = "Unpaid"
    enrollments = [
        {"course_code": "CS111", "course_title": "Introduction to Computing", "units": 4, "fee": 850.00},
        {"course_code": "MA101", "course_title": "Calculus I", "units": 4, "fee": 850.00}
    ]

    return render_template('fees.html',
                           total_fees=total_fees,
                           holds=holds,
                           fee_status=fee_status,
                           enrollments=enrollments)