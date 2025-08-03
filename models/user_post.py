"""
UserPost model for tracking user-post interactions and user-created posts.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime
import enum

class PostStatus(enum.Enum):
    """Post status enumeration for user posts"""
    DRAFT = "draft"
    PUBLISHED = "published"
    MODERATED = "moderated"
    REJECTED = "rejected"

class UserPost(BaseModel, db.Model):
    """UserPost model for user-created posts and interactions"""
    __tablename__ = 'user_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)  # For interactions
    
    # User-created post fields
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    salary_currency = db.Column(db.String(10), default='RUB')
    company_name = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_telegram = db.Column(db.String(80), nullable=True)
    status = db.Column(db.Enum(PostStatus), default=PostStatus.DRAFT)
    views = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    
    # Interaction fields
    is_read = db.Column(db.Boolean, default=False)
    is_bookmarked = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    bookmarked_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='posts')
    post = db.relationship('Post', back_populates='user_posts')
    statistics = db.relationship('PostStatistics', back_populates='user_post', uselist=False)
    
    def __init__(self, user_id, post_id=None, title=None, content=None, **kwargs):
        self.user_id = user_id
        self.post_id = post_id
        self.title = title
        self.content = content
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        if self.title:
            return f'<UserPost "{self.title}" by user {self.user_id}>'
        return f'<UserPost interaction user_id={self.user_id} post_id={self.post_id}>'
    
    @property
    def is_expired(self):
        """Check if post has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def is_published(self):
        """Check if post is published"""
        return self.status == PostStatus.PUBLISHED
    
    @property
    def is_user_created_post(self):
        """Check if this is a user-created post vs interaction"""
        return self.title is not None and self.content is not None
    
    def publish(self):
        """Publish the post"""
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        return self.save()
    
    def mark_as_read(self):
        """Mark post as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            return self.save()
        return self
    
    def toggle_bookmark(self):
        """Toggle bookmark status"""
        self.is_bookmarked = not self.is_bookmarked
        self.bookmarked_at = datetime.utcnow() if self.is_bookmarked else None
        return self.save()
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        return self.save()
    
    def get_salary_range(self):
        """Get formatted salary range"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} - {self.salary_max:,} {self.salary_currency}"
        elif self.salary_min:
            return f"от {self.salary_min:,} {self.salary_currency}"
        elif self.salary_max:
            return f"до {self.salary_max:,} {self.salary_currency}"
        return "Не указана"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'city': self.city,
            'salary_range': self.get_salary_range() if self.is_user_created_post else None,
            'company_name': self.company_name,
            'status': self.status.value if self.is_user_created_post else None,
            'views': self.views,
            'is_read': self.is_read,
            'is_bookmarked': self.is_bookmarked,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def get_user_interactions(cls, user_id, limit=20, offset=0):
        """Get user's post interactions"""
        return cls.query.filter_by(user_id=user_id).filter(cls.post_id != None).offset(offset).limit(limit).all()
    
    @classmethod
    def get_user_created_posts(cls, user_id, status=None, limit=20, offset=0):
        """Get user's created posts"""
        query = cls.query.filter_by(user_id=user_id).filter(cls.title != None)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).offset(offset).limit(limit).all()
    
    @classmethod
    def get_published_posts(cls, limit=20, offset=0):
        """Get all published user posts"""
        return cls.query.filter_by(status=PostStatus.PUBLISHED).filter(cls.title != None).order_by(cls.published_at.desc()).offset(offset).limit(limit).all()
