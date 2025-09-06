"""
Super Tic-Tac-Toe Flask Application Factory
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_name=None):
    """Create and configure the Flask application."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.game import game_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp, url_prefix='/game')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register WebSocket events
    from app.routes.websocket import register_socketio_events
    register_socketio_events(socketio)
    
    # Create database tables with error handling
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
            if not app.config.get('TESTING'):
                raise
    
    # Add error handlers for production
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        return render_template('errors/503.html'), 503
    
    return app
