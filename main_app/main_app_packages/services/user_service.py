from flask import current_app
from ..models import db, User
from ..audit import audit_service, audit_operation

class UserService:
    """Service for user-related operations"""
    
    @audit_service('user_service')
    def get_user(self, user_id):
        """Get a user by ID"""
        return User.query.get(user_id)
    
    @audit_service('user_service')
    def create_user(self, user_data):
        """Create a new user"""
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user
    
    @audit_service('user_service')
    def update_user(self, user_id, user_data):
        """Update an existing user"""
        user = self.get_user(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            db.session.commit()
        return user
    
    @audit_service('user_service')
    def delete_user(self, user_id):
        """Delete a user"""
        user = self.get_user(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    
    @audit_operation('user_login')
    def login(self, username, password):
        """Handle user login"""
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    @audit_operation('user_logout')
    def logout(self, user_id):
        """Handle user logout"""
        user = self.get_user(user_id)
        if user:
            # Perform any necessary cleanup
            return True
        return False
    
    @audit_operation('password_change')
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        user = self.get_user(user_id)
        if user and user.check_password(old_password):
            user.set_password(new_password)
            db.session.commit()
            return True
        return False
    
    @audit_operation('profile_update')
    def update_profile(self, user_id, profile_data):
        """Update user profile"""
        user = self.get_user(user_id)
        if user:
            for key, value in profile_data.items():
                setattr(user, key, value)
            db.session.commit()
            return user
        return None 