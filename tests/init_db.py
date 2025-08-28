#!/usr/bin/env python3
"""
Database initialization script for Super Tic-Tac-Toe
Creates all tables and sets up the database schema
"""

from app import create_app, db
from app.models import User, Game, GameMove, Room

def init_database():
    """Initialize the database with all tables."""
    app = create_app()
    
    with app.app_context():
        print("🗄️  Initializing database...")
        
        # Drop all tables (for clean setup)
        print("📋 Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("🏗️  Creating database tables...")
        db.create_all()
        
        # Create a test admin user
        print("👤 Creating test admin user...")
        admin_user = User(
            username='admin',
            email='admin@supertictactoe.com'
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        
        # Create a test guest user
        print("🎭 Creating test guest user...")
        guest_user = User(
            username='Guest_123456'
        )
        guest_user.set_password('guest_password')
        
        db.session.add(guest_user)
        
        # Commit the changes
        db.session.commit()
        
        print("✅ Database initialization complete!")
        print(f"📊 Created {User.query.count()} users")
        print(f"🎮 Created {Game.query.count()} games")
        print(f"🏠 Created {Room.query.count()} rooms")
        
        print("\n🔐 Test Accounts Created (DEVELOPMENT ONLY):")
        print("   Admin: username='admin', password='admin123'")
        print("   Guest: username='Guest_123456', password='guest_password'")
        print("   ⚠️  These are test credentials - change in production!")

if __name__ == '__main__':
    init_database()
