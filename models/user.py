"""
User model for user management.
"""
from flask_login import UserMixin
from .base import BaseModel
from core.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum

class UserRole(enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class User(BaseModel, UserMixin, db.Model):
    """User model for storing user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('UserPost', back_populates='user', lazy='dynamic')
    subscriptions = db.relationship('UserSubscription', back_populates='user', lazy='dynamic')
    
    def __init__(self, username, email, password, role=UserRole.USER):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_moderator(self):
        """Check if user is moderator"""
        return self.role == UserRole.MODERATOR
    
    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email).first()
    
    def is_subscribed_to_category(self, category_id):
        """Check if user is subscribed to a category"""
        return self.subscriptions.filter_by(category_id=category_id).first() is not None
