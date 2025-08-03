"""
Flask extensions initialization.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    """Initialize Flask extensions with app."""
    
    # Database only
    db.init_app(app)
    migrate.init_app(app, db)

def register_blueprints(app):
    """Register application blueprints."""
    
    # Import blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
