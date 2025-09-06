import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-not-for-production-use-only'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///super_tictactoe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,  # Recycle connections after 1 hour
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Will be overridden in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Socket.IO configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Game configuration
    AI_THINK_TIME_LIMIT = 10  # seconds
    ROOM_CODE_LENGTH = 6
    MAX_SPECTATORS_PER_ROOM = 10
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Security headers
    FORCE_HTTPS = False  # Will be overridden in production

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Override with environment secret key in production (safer default)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-THIS-IN-PRODUCTION-NOT-SECURE'
    
    # Production database configuration
    # Supports PostgreSQL, MySQL, and SQLite
    # Example PostgreSQL: postgresql://user:password@host:port/dbname
    # Example MySQL: mysql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///super_tictactoe.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 20,  # Connection pool size
        'max_overflow': 30,  # Additional connections beyond pool_size
        'pool_timeout': 30,  # Timeout for getting connection from pool
    }
    
    # Production security settings
    SESSION_COOKIE_SECURE = True  # HTTPS only cookies
    FORCE_HTTPS = True
    
    # Production Socket.IO
    SOCKETIO_ASYNC_MODE = 'gevent'  # Better for production
    
    # Production rate limiting (more strict)
    RATELIMIT_DEFAULT = "50 per hour"

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
