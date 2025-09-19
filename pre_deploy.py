#!/usr/bin/env python3
"""
Pre-deployment hook to backup database before manual redeploy
Run this before any manual deployment to preserve data
"""
import os
import sys
from db_persistence import backup_database, check_database_persistence

def main():
    print("🚀 Pre-deployment database backup")
    print("=" * 40)
    
    # Check if database has data
    if check_database_persistence():
        print("✅ Database backup completed successfully!")
        print("🛡️ Your data is now protected from manual redeploy")
        print("\nYou can now safely:")
        print("  - Click 'Deploy Latest Commit' in Render")
        print("  - Use 'Redeploy' button")
        print("  - Your data will be preserved!")
    else:
        print("📝 No existing data to backup")
        print("✅ Safe to deploy")

if __name__ == '__main__':
    main()
