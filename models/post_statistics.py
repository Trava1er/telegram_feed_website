"""
PostStatistics model for tracking post engagement metrics.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime, date

class PostStatistics(BaseModel, db.Model):
    """PostStatistics model for tracking post engagement"""
    __tablename__ = 'post_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_post_id = db.Column(db.Integer, db.ForeignKey('user_posts.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    views = db.Column(db.Integer, default=0, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)
    contact_views = db.Column(db.Integer, default=0, nullable=False)
    shares = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_post = db.relationship('UserPost', back_populates='statistics')
    post = db.relationship('Post', back_populates='statistics')
    
    # Unique constraint for daily statistics
    __table_args__ = (db.UniqueConstraint('user_post_id', 'date', name='unique_daily_user_post_stats'),)
    
    def __init__(self, user_post_id, post_id=None, date=None):
        self.user_post_id = user_post_id
        self.post_id = post_id
        self.date = date or datetime.utcnow().date()
    
    def __repr__(self):
        return f'<PostStatistics user_post_id={self.user_post_id} date={self.date}>'
    
    @classmethod
    def get_or_create_today(cls, user_post_id, post_id=None):
        """Get or create statistics record for today"""
        today = date.today()
        stats = cls.query.filter_by(user_post_id=user_post_id, date=today).first()
        
        if not stats:
            stats = cls(user_post_id=user_post_id, post_id=post_id, date=today)
            stats = stats.save()
        
        return stats
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        return self.save()
    
    def increment_clicks(self):
        """Increment click count"""
        self.clicks += 1
        return self.save()
    
    def increment_contact_views(self):
        """Increment contact view count"""
        self.contact_views += 1
        return self.save()
    
    def increment_shares(self):
        """Increment share count"""
        self.shares += 1
        return self.save()
    
    @property
    def ctr(self):
        """Calculate click-through rate"""
        if self.views > 0:
            return round((self.clicks / self.views) * 100, 2)
        return 0.0
    
    @property
    def contact_ctr(self):
        """Calculate contact click-through rate"""
        if self.views > 0:
            return round((self.contact_views / self.views) * 100, 2)
        return 0.0
    
    @property
    def share_rate(self):
        """Calculate share rate"""
        if self.views > 0:
            return round((self.shares / self.views) * 100, 2)
        return 0.0
    
    def to_dict(self):
        """Convert statistics to dictionary for API responses"""
        return {
            'id': self.id,
            'user_post_id': self.user_post_id,
            'post_id': self.post_id,
            'date': self.date.isoformat(),
            'views': self.views,
            'clicks': self.clicks,
            'contact_views': self.contact_views,
            'shares': self.shares,
            'ctr': self.ctr,
            'contact_ctr': self.contact_ctr,
            'share_rate': self.share_rate,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def get_stats_by_date_range(cls, user_post_id, start_date, end_date):
        """Get statistics for a date range"""
        return cls.query.filter(
            cls.user_post_id == user_post_id,
            cls.date >= start_date,
            cls.date <= end_date
        ).order_by(cls.date).all()
    
    @classmethod
    def get_total_stats(cls, user_post_id):
        """Get total statistics for a user post"""
        from sqlalchemy import func
        result = db.session.query(
            func.sum(cls.views).label('total_views'),
            func.sum(cls.clicks).label('total_clicks'),
            func.sum(cls.contact_views).label('total_contact_views'),
            func.sum(cls.shares).label('total_shares')
        ).filter_by(user_post_id=user_post_id).first()
        
        return {
            'total_views': result.total_views or 0,
            'total_clicks': result.total_clicks or 0,
            'total_contact_views': result.total_contact_views or 0,
            'total_shares': result.total_shares or 0
        }
