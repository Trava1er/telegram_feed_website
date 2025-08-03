"""
Post model for storing feed posts with contact extraction.
"""
from .base import BaseModel
from core.extensions import db
from datetime import datetime
import hashlib
import json

class Post(BaseModel, db.Model):
    """Post model for storing feed posts"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_message_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(500))
    media_type = db.Column(db.String(50))  # photo, video, document, etc.
    feed_id = db.Column(db.Integer, db.ForeignKey('feeds.id'), nullable=False)
    telegram_date = db.Column(db.DateTime, nullable=False, index=True)
    is_edited = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0, nullable=False)
    
    # Contact extraction results
    contacts_extracted = db.Column(db.Boolean, default=False, nullable=False)
    phone_numbers = db.Column(db.JSON, nullable=True)
    emails = db.Column(db.JSON, nullable=True)
    telegram_users = db.Column(db.JSON, nullable=True)
    urls = db.Column(db.JSON, nullable=True)
    
    # Duplicate detection fields
    content_hash = db.Column(db.String(64), index=True)
    duplicate_group_id = db.Column(db.String(36), index=True)
    is_primary_duplicate = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feed = db.relationship('Feed', back_populates='posts')
    user_posts = db.relationship('UserPost', back_populates='post', lazy='dynamic')
    statistics = db.relationship('PostStatistics', back_populates='post', uselist=False)
    
    def __init__(self, telegram_message_id, content, feed_id, telegram_date, 
                 media_url=None, media_type=None, is_edited=False, views=0):
        self.telegram_message_id = telegram_message_id
        self.content = content
        self.feed_id = feed_id
        self.telegram_date = telegram_date
        self.media_url = media_url
        self.media_type = media_type
        self.is_edited = is_edited
        self.views = views
        self.content_hash = self.generate_content_hash()
    
    def __repr__(self):
        return f'<Post {self.id} from {self.feed.name if self.feed else "Unknown"}>'
    
    def generate_content_hash(self):
        """Generate SHA256 hash of normalized content for duplicate detection"""
        if self.content:
            normalized_content = self.content.strip().lower()
            return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
        return None
    
    def set_contacts(self, contacts):
        """Set contacts from extracted data"""
        if contacts:
            self.phone_numbers = contacts.get('phone_numbers') if contacts.get('phone_numbers') else None
            self.emails = contacts.get('emails') if contacts.get('emails') else None  
            self.telegram_users = contacts.get('telegram_users') if contacts.get('telegram_users') else None
            self.urls = contacts.get('urls') if contacts.get('urls') else None
            self.contacts_extracted = True
    
    def extract_and_save_contacts(self):
        """Extract contact information from content and save to database"""
        if not self.contacts_extracted and self.content:
            import re
            
            # Simple contact extraction
            phone_pattern = r'(?:\+7|8)[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
            phones = re.findall(phone_pattern, self.content)
            
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, self.content)
            
            telegram_pattern = r'@[A-Za-z0-9_]{5,}'
            telegrams = re.findall(telegram_pattern, self.content)
            
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, self.content)
            
            contacts = {
                'phone_numbers': phones,
                'emails': emails,
                'telegram_users': telegrams,
                'urls': urls
            }
            
            # Only save non-empty lists
            self.phone_numbers = contacts['phone_numbers'] if contacts['phone_numbers'] else None
            self.emails = contacts['emails'] if contacts['emails'] else None
            self.telegram_users = contacts['telegram_users'] if contacts['telegram_users'] else None
            self.urls = contacts['urls'] if contacts['urls'] else None
            self.contacts_extracted = True
    
    def get_contacts_dict(self):
        """Get contacts as a dictionary for template rendering"""
        return {
            'phone_numbers': self.phone_numbers or [],
            'emails': self.emails or [],
            'telegram_users': self.telegram_users or [],
            'urls': self.urls or []
        }
    
    def has_contacts(self):
        """Check if post has any contact information"""
        return any([
            self.phone_numbers,
            self.emails, 
            self.telegram_users,
            self.urls
        ])
    
    def to_dict(self):
        return {
            'id': self.id,
            'telegram_message_id': self.telegram_message_id,
            'content': self.content,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'feed_id': self.feed_id,
            'feed_name': self.feed.name if self.feed else None,
            'telegram_date': self.telegram_date.isoformat(),
            'is_edited': self.is_edited,
            'content_hash': self.content_hash,
            'duplicate_group_id': self.duplicate_group_id,
            'is_primary_duplicate': self.is_primary_duplicate,
            'contacts': self.get_contacts_dict(),
            'has_contacts': self.has_contacts(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def get_posts_with_filters(cls, feed_id=None, hide_duplicates=False, limit=20, offset=0):
        """Get posts with optional filtering"""
        query = cls.query
        
        if feed_id:
            query = query.filter_by(feed_id=feed_id)
        
        if hide_duplicates:
            query = query.filter(
                db.or_(
                    cls.is_primary_duplicate == True,
                    cls.duplicate_group_id.is_(None)
                )
            )
        
        return query.order_by(cls.telegram_date.desc()).offset(offset).limit(limit).all()
    
    @classmethod
    def get_posts_with_contacts(cls, limit=20, offset=0):
        """Get posts that have contact information"""
        return cls.query.filter(
            db.or_(
                cls.phone_numbers != None,
                cls.emails != None,
                cls.telegram_users != None,
                cls.urls != None
            )
        ).order_by(cls.telegram_date.desc()).offset(offset).limit(limit).all()
    
    @classmethod
    def get_by_telegram_message_id(cls, telegram_message_id, feed_id):
        """Get post by telegram message ID and feed ID"""
        return cls.query.filter_by(telegram_message_id=telegram_message_id, feed_id=feed_id).first()
