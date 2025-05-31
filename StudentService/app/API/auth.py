import os
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template, session, redirect, url_for
from werkzeug.security import check_password_hash
import sqlite3
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_student_db_path():
    """Get the path to the StudentService database"""
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'instance', 'studentservice.db'
    ))

def get_sas_db_path():
    """Get the path to the SAS_Services database"""
    return os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'SAS_Services', 'instance', 'enrollment.db'
    ))

@auth_bp.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@auth_bp.route('/api/login', methods=['POST'])
def login_post():
    """
    Handle JSON login (POST /api/login).
    Expects { role, password, email } in the JSON body.
    """
    data = request.get_json() or {}
    role = data.get('role')
    password = data.get('password')
    email = data.get('email', '')

    if role != 'student' or not password:
        return jsonify({'message': 'Missing or invalid fields'}), 400

    if not re.match(r'^s\d{8}@student\.usp\.ac\.fj$', email):
        return jsonify({'message': 'Invalid student email format'}), 400

    try:
        # Connect to the StudentService database
        db_path = get_student_db_path()
        if not os.path.exists(db_path):
            return jsonify({'message': 'Student database not found'}), 500

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get student details from the Student table
        cursor.execute("""
            SELECT StudentID, Email, PasswordHash, FirstName, LastName
            FROM Student 
            WHERE Email = ?
        """, (email,))
        student = cursor.fetchone()

        if not student:
            return jsonify({'message': 'Invalid credentials'}), 401

        student_id, student_email, password_hash, first_name, last_name = student

        # Verify password
        if not check_password_hash(password_hash, password):
            return jsonify({'message': 'Invalid credentials'}), 401

        # Store user info in session
        session['user_id'] = student_id
        session['email'] = student_email
        session['username'] = f"{first_name} {last_name}"
        session['role'] = 'student'

        return jsonify({
            'success': True,
            'redirect': url_for('home')
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'message': 'An error occurred during login'}), 500

    finally:
        if 'conn' in locals():
            conn.close()

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
