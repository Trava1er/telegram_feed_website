"""
UserSubscription model for managing user subscriptions to categories.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime
import enum

class SubscriptionStatus(enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    EXPIRED = "expired"

class UserSubscription(BaseModel, db.Model):
    """UserSubscription model for user category subscriptions"""
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='subscriptions')
    category = db.relationship('Category', back_populates='subscriptions')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'category_id', name='unique_user_category_subscription'),)
    
    def __init__(self, user_id, category_id, status=SubscriptionStatus.ACTIVE, notifications_enabled=True):
        self.user_id = user_id
        self.category_id = category_id
        self.status = status
        self.notifications_enabled = notifications_enabled
    
    def __repr__(self):
        return f'<UserSubscription user_id={self.user_id} category_id={self.category_id}>'
    
    def activate(self):
        """Activate subscription"""
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        return self.save()
    
    def deactivate(self):
        """Deactivate subscription"""
        self.status = SubscriptionStatus.INACTIVE
        self.updated_at = datetime.utcnow()
        return self.save()
    
    def pause(self):
        """Pause subscription"""
        self.status = SubscriptionStatus.PAUSED
        self.updated_at = datetime.utcnow()
        return self.save()
    
    def expire(self):
        """Mark subscription as expired"""
        self.status = SubscriptionStatus.EXPIRED
        self.updated_at = datetime.utcnow()
        return self.save()
    
    def is_active(self):
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE
    
    def toggle_notifications(self):
        """Toggle notification settings"""
        self.notifications_enabled = not self.notifications_enabled
        self.updated_at = datetime.utcnow()
        return self.save()
    
    def to_dict(self):
        """Convert subscription to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'status': self.status.value,
            'notifications_enabled': self.notifications_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_user_subscriptions(cls, user_id, status=None):
        """Get user's subscriptions, optionally filtered by status"""
        query = cls.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.all()
    
    @classmethod
    def get_category_subscribers(cls, category_id, status=SubscriptionStatus.ACTIVE):
        """Get subscribers for a category"""
        return cls.query.filter_by(category_id=category_id, status=status).all()
