"""
Routes package - Contains all Flask blueprints and route handlers
"""

from .main import main_bp
from .auth import auth_bp  
from .account import account_bp
from .admin import admin_bp
from .api import api_bp

# Export all blueprints for easy importing
__all__ = ['main_bp', 'auth_bp', 'account_bp', 'admin_bp', 'api_bp']