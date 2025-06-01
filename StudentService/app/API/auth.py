import os
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
import sqlite3
from functools import wraps
from app.Core.models import db, Student
from sqlalchemy import func

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db_path():
    """Get the absolute path to the studentservice.db"""
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'instance',
        'studentservice.db'
    ))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Handle JSON request
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({
                    'message': 'Please provide both email and password'
                }), 400

            # Extract student ID from email and convert to uppercase
            student_id = email.split('@')[0] if '@' in email else email
            student_id = student_id.upper()  # Convert to uppercase to match database

            try:
                # Query the Student table using SQLAlchemy with case-insensitive comparison
                student = Student.query.filter(func.upper(Student.StudentID) == student_id).first()

                if not student:
                    current_app.logger.warning(f"Login attempt failed: Student ID {student_id} not found")
                    return jsonify({
                        'message': 'Invalid credentials'
                    }), 401

                # Check password using the Student model's method
                if not student.check_password(password):
                    current_app.logger.warning(f"Login attempt failed: Invalid password for Student ID {student_id}")
                    return jsonify({
                        'message': 'Invalid credentials'
                    }), 401

                # Store user info in session
                session['user_id'] = student.StudentID
                session['student_id'] = student.StudentID
                session['email'] = student.Email
                session['username'] = f"{student.FirstName} {student.LastName}"
                session['role'] = 'student'

                current_app.logger.info(f"Successful login for Student ID {student_id}")
                return jsonify({
                    'message': 'Login successful',
                    'redirect': url_for('root')  # Changed to redirect to root which will handle the home redirect
                })

            except Exception as e:
                current_app.logger.error(f"Login error for Student ID {student_id}: {str(e)}")
                return jsonify({
                    'message': f'An error occurred during login: {str(e)}'
                }), 500

        # Handle form data request
        else:
            student_id = request.form.get('studentId')
            password = request.form.get('password')

            if not student_id or not password:
                flash('Please provide both Student ID and password', 'error')
                return render_template('login.html')

            try:
                # Extract student ID from email if email format is used and convert to uppercase
                if '@' in student_id:
                    student_id = student_id.split('@')[0]
                student_id = student_id.upper()  # Convert to uppercase to match database

                # Query the Student table using SQLAlchemy with case-insensitive comparison
                student = Student.query.filter(func.upper(Student.StudentID) == student_id).first()

                if not student:
                    current_app.logger.warning(f"Login attempt failed: Student ID {student_id} not found")
                    flash('Invalid Student ID or password', 'error')
                    return render_template('login.html')

                # Check password using the Student model's method
                if not student.check_password(password):
                    current_app.logger.warning(f"Login attempt failed: Invalid password for Student ID {student_id}")
                    flash('Invalid Student ID or password', 'error')
                    return render_template('login.html')

                # Store user info in session
                session['user_id'] = student.StudentID
                session['student_id'] = student.StudentID
                session['email'] = student.Email
                session['username'] = f"{student.FirstName} {student.LastName}"
                session['role'] = 'student'

                current_app.logger.info(f"Successful login for Student ID {student_id}")
                return redirect(url_for('home'))

            except Exception as e:
                current_app.logger.error(f"Login error for Student ID {student_id}: {str(e)}")
                flash('An error occurred during login. Please try again.', 'error')
                return render_template('login.html')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))