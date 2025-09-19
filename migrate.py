#!/usr/bin/env python3
"""
Database migration script for Super Tic-Tac-Toe
Run this after deploying new code to handle database schema changes
"""
import os
import sys
from app import create_app, db
from app.models import User, Game, GameMove, Room

def migrate_database():
    """Run database migrations safely."""
    print("🔄 Running database migrations...")
    
    app = create_app('production')
    with app.app_context():
        try:
            # Create any new tables/columns
            db.create_all()
            print("✅ Database schema updated")
            
            # Add any new default data if needed
            # (Only add if it doesn't exist)
            
            print("🎉 Migration complete!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == '__main__':
    migrate_database()
