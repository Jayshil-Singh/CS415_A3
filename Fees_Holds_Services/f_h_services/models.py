from . import db
from datetime import datetime

class Fee(db.Model):
    __tablename__ = 'fees'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'amount': self.amount,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid': self.paid,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Hold(db.Model):
    __tablename__ = 'holds'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'FINANCIAL', 'ACADEMIC', 'DISCIPLINARY'
    description = db.Column(db.String(200), nullable=False)
    placed_date = db.Column(db.DateTime, default=datetime.utcnow)
    release_date = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    placed_by = db.Column(db.String(100), nullable=False)
    released_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'type': self.type,
            'description': self.description,
            'placed_date': self.placed_date.isoformat(),
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'active': self.active,
            'placed_by': self.placed_by,
            'released_by': self.released_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class PaymentHistory(db.Model):
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    fee_id = db.Column(db.Integer, db.ForeignKey('fees.id'), nullable=False)
    student_id = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'SUCCESS', 'PENDING', 'FAILED'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fee = db.relationship('Fee', backref=db.backref('payments', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'fee_id': self.fee_id,
            'student_id': self.student_id,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat(),
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        } 