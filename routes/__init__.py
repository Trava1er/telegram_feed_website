"""
Routes package - Contains all Flask blueprints and route handlers
"""

from .main import main_bp
from .api import api_bp

# Export all blueprints for easy importing
__all__ = ['main_bp', 'api_bp']