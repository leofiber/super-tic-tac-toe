#!/usr/bin/env python3
"""
Quick deployment script for Super Tic-Tac-Toe
"""
import os
import sys
import subprocess
import secrets
from app import create_app, db
from app.models import User, Game, Room

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

def init_production_db():
    """Initialize the production database."""
    print("🔧 Initializing production database...")
    
    app = create_app('production')
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create a test admin user (optional)
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(username='admin', email='admin@example.com')
                admin_user.set_password('admin123')  # Change this!
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created (username: admin, password: admin123)")
                print("⚠️  IMPORTANT: Change the admin password immediately!")
            
            print("🎉 Database initialization complete!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

def check_requirements():
    """Check if all required packages are installed."""
    print("📦 Checking requirements...")
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_socketio
        import gunicorn
        import gevent
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    """Main deployment function."""
    print("🚀 Super Tic-Tac-Toe Production Deployment")
    print("=" * 50)
    
    # Check if we're in production mode
    if os.environ.get('FLASK_CONFIG') != 'production':
        print("⚠️  Setting FLASK_CONFIG=production")
        os.environ['FLASK_CONFIG'] = 'production'
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("Set it to your production database URL:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/db'")
        sys.exit(1)
    
    print(f"📊 Using database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    # Check secret key
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key or secret_key == 'dev-key-not-for-production-use-only':
        print("⚠️  SECRET_KEY not set or using default!")
        new_key = generate_secret_key()
        print(f"Generated new secret key: {new_key}")
        print("Set it with: export SECRET_KEY='your-secret-key'")
        os.environ['SECRET_KEY'] = new_key
    
    # Initialize database
    if not init_production_db():
        sys.exit(1)
    
    print("\n🎉 Deployment setup complete!")
    print("\nNext steps:")
    print("1. Start the application with: gunicorn --worker-class gevent --workers 1 --worker-connections 1000 --bind 0.0.0.0:8000 run:app")
    print("2. Or use the Procfile for Heroku deployment")
    print("3. Make sure to change the admin password!")

if __name__ == '__main__':
    main()
