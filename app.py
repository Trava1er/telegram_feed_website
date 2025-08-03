"""
Flask application factory for Telegram Feed Website.
"""
import os
import re
from flask import Flask
from flask_migrate import Migrate

def create_app(config_name=None):
    """
    Create Flask application using the factory pattern.
    
    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration from environment
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Telegram configuration
    app.config['TELEGRAM_BOT_TOKEN'] = os.getenv('TELEGRAM_BOT_TOKEN')
    app.config['TELEGRAM_API_ID'] = os.getenv('TELEGRAM_API_ID')
    app.config['TELEGRAM_API_HASH'] = os.getenv('TELEGRAM_API_HASH')
    app.config['TELEGRAM_SESSION_NAME'] = os.getenv('TELEGRAM_SESSION_NAME', 'telegram_bot')
    app.config['TELEGRAM_WEBHOOK_URL'] = os.getenv('TELEGRAM_WEBHOOK_URL')
    
    # Add custom Jinja2 filters
    @app.template_filter('clean_text')
    def clean_text_filter(text):
        """Clean text by removing HTML tags and excessive whitespace."""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', str(text))
        # Remove multiple whitespaces and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    try:
        print("Step 1: Starting app initialization...")
        
        # Initialize extensions (only database, no authentication)
        print("Step 2: Importing core extensions...")
        from core.extensions import db
        
        print("Step 3: Initializing database...")
        db.init_app(app)
        
        print("Step 4: Initializing Flask-Migrate...")
        migrate = Migrate(app, db)
        
        print("Step 5: Importing blueprints...")
        from routes.main import main_bp
        from routes.api import api_bp
        
        print("Step 6: Registering blueprints...")
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
        
        print("Step 7: Creating database tables...")
        with app.app_context():
            db.create_all()
            
        print("Step 8: Registering CLI commands...")
        from services import cli
        cli.init_app(app)
            
        print("✅ Full application loaded successfully!")
        return app
            
    except Exception as e:
        # If any import fails, log and continue with basic app
        print(f"❌ Application initialization failed at some step: {e}")
        print("Running in basic mode...")
        import traceback
        traceback.print_exc()
        
        from flask import jsonify
        
        @app.route('/')
        def home():
            return jsonify({
                "status": "OK", 
                "message": "Telegram Feed Website is running!",
                "version": "1.0.0"
            })
            
        @app.route('/health')
        def health():
            return jsonify({"status": "healthy"})
    
    return app

# Create app instance for Gunicorn
app = create_app('production')

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)