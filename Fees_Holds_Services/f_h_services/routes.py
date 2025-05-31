from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from .models import db, Fee, Hold, PaymentHistory
from functools import wraps
import jwt
import os

fnh_bp = Blueprint('fnh', __name__)
fees_bp = Blueprint('fees', __name__, url_prefix='/api/fees')
holds_bp = Blueprint('holds', __name__, url_prefix='/api/holds')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            secret_key = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            if data['role'] not in ['admin', 'sas_manager']:
                return jsonify({'message': 'Insufficient permissions!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated

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

# Fee Routes
@fees_bp.route('/', methods=['GET'])
@token_required
def get_all_fees():
    student_id = request.args.get('student_id')
    if student_id:
        fees = Fee.query.filter_by(student_id=student_id).all()
    else:
        fees = Fee.query.all()
    return jsonify([fee.to_dict() for fee in fees])

@fees_bp.route('/<int:fee_id>', methods=['GET'])
@token_required
def get_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    return jsonify(fee.to_dict())

@fees_bp.route('/', methods=['POST'])
@token_required
def create_fee():
    data = request.get_json()
    
    required_fields = ['student_id', 'amount', 'description', 'due_date']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        fee = Fee(
            student_id=data['student_id'],
            amount=data['amount'],
            description=data['description'],
            due_date=due_date
        )
        db.session.add(fee)
        db.session.commit()
        return jsonify(fee.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@fees_bp.route('/<int:fee_id>', methods=['PUT'])
@token_required
def update_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    data = request.get_json()
    
    try:
        if 'amount' in data:
            fee.amount = data['amount']
        if 'description' in data:
            fee.description = data['description']
        if 'due_date' in data:
            fee.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        if 'paid' in data:
            fee.paid = data['paid']
            if data['paid']:
                fee.payment_date = datetime.utcnow()
        
        db.session.commit()
        return jsonify(fee.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@fees_bp.route('/<int:fee_id>/pay', methods=['POST'])
@token_required
def process_payment(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    if fee.paid:
        return jsonify({'message': 'Fee has already been paid'}), 400
    
    data = request.get_json()
    required_fields = ['payment_method', 'transaction_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        # Record payment
        payment = PaymentHistory(
            fee_id=fee.id,
            student_id=fee.student_id,
            amount=fee.amount,
            payment_method=data['payment_method'],
            transaction_id=data['transaction_id'],
            status='SUCCESS'
        )
        
        # Update fee
        fee.paid = True
        fee.payment_date = datetime.utcnow()
        fee.payment_method = data['payment_method']
        fee.transaction_id = data['transaction_id']
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment processed successfully',
            'fee': fee.to_dict(),
            'payment': payment.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# Hold Routes
@holds_bp.route('/', methods=['GET'])
@token_required
def get_all_holds():
    student_id = request.args.get('student_id')
    active_only = request.args.get('active_only', 'false').lower() == 'true'
    
    query = Hold.query
    if student_id:
        query = query.filter_by(student_id=student_id)
    if active_only:
        query = query.filter_by(active=True)
    
    holds = query.all()
    return jsonify([hold.to_dict() for hold in holds])

@holds_bp.route('/<int:hold_id>', methods=['GET'])
@token_required
def get_hold(hold_id):
    hold = Hold.query.get_or_404(hold_id)
    return jsonify(hold.to_dict())

@holds_bp.route('/', methods=['POST'])
@token_required
def create_hold():
    data = request.get_json()
    
    required_fields = ['student_id', 'type', 'description', 'placed_by']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        hold = Hold(
            student_id=data['student_id'],
            type=data['type'],
            description=data['description'],
            placed_by=data['placed_by']
        )
        db.session.add(hold)
        db.session.commit()
        return jsonify(hold.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@holds_bp.route('/<int:hold_id>/release', methods=['POST'])
@token_required
def release_hold(hold_id):
    hold = Hold.query.get_or_404(hold_id)
    if not hold.active:
        return jsonify({'message': 'Hold is already released'}), 400
    
    data = request.get_json()
    if 'released_by' not in data:
        return jsonify({'message': 'Missing released_by field'}), 400
    
    try:
        hold.active = False
        hold.release_date = datetime.utcnow()
        hold.released_by = data['released_by']
        db.session.commit()
        return jsonify(hold.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400