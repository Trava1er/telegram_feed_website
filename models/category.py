"""
Category model for organizing posts by categories.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime

class Category(BaseModel, db.Model):
    """Category model for organizing posts"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    icon = db.Column(db.String(50))  # Icon class name
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feeds = db.relationship('Feed', back_populates='category', lazy='dynamic')
    subscriptions = db.relationship('UserSubscription', back_populates='category', lazy='dynamic')
    
    def __init__(self, name, display_name, description=None, color='#007bff', icon=None, sort_order=0):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.color = color
        self.icon = icon
        self.sort_order = sort_order
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'feeds_count': self.get_feed_count()
        }
    
    @classmethod
    def get_by_name(cls, name):
        """Get category by name"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_active_categories(cls):
        """Get all categories ordered by sort_order"""
        return cls.query.order_by('sort_order').all()
    
    def get_feed_count(self):
        """Get number of feeds in this category"""
        return self.feeds.count()
    
    def get_subscriber_count(self):
        """Get number of users subscribed to this category"""
        from .user_subscription import SubscriptionStatus
        return self.subscriptions.filter_by(status=SubscriptionStatus.ACTIVE).count()
