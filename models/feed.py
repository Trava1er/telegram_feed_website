"""
Feed model for RSS/Telegram feed management.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime

class Feed(BaseModel, db.Model):
    """Feed model for RSS/Telegram feeds"""
    __tablename__ = 'feeds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    telegram_channel_id = db.Column(db.String(100))  # @channel_name or -100123456789
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    sync_frequency = db.Column(db.Integer, default=3600)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', back_populates='feeds')
    posts = db.relationship('Post', back_populates='feed', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, url, telegram_channel_id=None, description=None, 
                 category_id=None, is_active=True, sync_frequency=3600):
        self.name = name
        self.url = url
        self.telegram_channel_id = telegram_channel_id
        self.description = description
        self.category_id = category_id
        self.is_active = is_active
        self.sync_frequency = sync_frequency
    
    def __repr__(self):
        return f'<Feed {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'telegram_channel_id': self.telegram_channel_id,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.display_name if self.category else None,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'posts_count': self.posts_count,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def posts_count(self):
        """Get posts count for this feed"""
        return self.posts.count()
    
    @classmethod
    def get_by_url(cls, url):
        """Get feed by URL"""
        return cls.query.filter_by(url=url).first()
    
    @classmethod
    def get_active_feeds(cls):
        """Get all active feeds"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_feeds_by_category(cls, category_id):
        """Get feeds by category"""
        return cls.query.filter_by(category_id=category_id, is_active=True).all()
    
    def get_recent_posts(self, limit=10):
        """Get recent posts from this feed"""
        from .post import Post
        return Post.query.filter_by(feed_id=self.id).order_by(Post.telegram_date.desc()).limit(limit).all()
    
    def update_last_sync(self):
        """Update last sync timestamp"""
        self.last_sync = datetime.utcnow()
        return self.save()
