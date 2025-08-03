"""
Models package for Telegram Feed Website

This package contains all database models organized by functionality.
Each model is in its own file with appropriate methods and relationships.
"""

# Import all models and enums
from core.extensions import db
from .category import Category
from .user import User, UserRole
from .feed import Feed
from .post import Post
from .user_post import UserPost, PostStatus
from .user_subscription import UserSubscription, SubscriptionStatus
from .post_statistics import PostStatistics

# Export all models and enums for easy importing
__all__ = [
    'db',
    'Category',
    'User', 'UserRole',
    'Feed',
    'Post',
    'UserPost', 'PostStatus',
    'UserSubscription', 'SubscriptionStatus',
    'PostStatistics'
]
