from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    if config_name == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode='gevent', cors_allowed_origins="*")
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import and register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.game import game_bp
    from app.routes.api import api_bp
    from app.routes.websocket import websocket_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(websocket_bp)
    
    # Import models
    from app.models import user, game, room
    
    # Create tables with persistence check
    with app.app_context():
        try:
            # Check if database exists and has data
            from app.models.user import User
            existing_users = User.query.count()
            
            if existing_users == 0:
                print("🔄 No existing data found, creating fresh database...")
                db.create_all()
                print("✅ Database tables created successfully")
            else:
                print(f"✅ Database exists with {existing_users} users - preserving data")
                # Only create missing tables, don't drop existing ones
                db.create_all()
                
        except Exception as e:
            print(f"⚠️ Database initialization: {e}")
            # Fallback: create tables anyway
            db.create_all()
            print("✅ Database tables created (fallback)")
    
    return app