"""
Base database configuration and shared utilities for all models.
"""
from core.extensions import db


class BaseModel(db.Model):
    """Base model with common functionality for all models"""
    __abstract__ = True
    
    def save(self):
        """Save the model to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the model from database"""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update model fields"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self.save()
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new instance and save to database"""
        instance = cls(**kwargs)
        return instance.save()
    
    @classmethod
    def get_by_id(cls, id):
        """Get instance by ID"""
        return cls.query.get(id)
    
    @classmethod
    def get_or_404(cls, id):
        """Get instance by ID or raise 404"""
        return cls.query.get_or_404(id)
