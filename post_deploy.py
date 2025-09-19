#!/usr/bin/env python3
"""
Post-deployment hook to restore database after manual redeploy
Run this after manual deployment to restore your data
"""
import os
import sys
import glob
from db_persistence import restore_database

def find_latest_backup():
    """Find the most recent backup file."""
    backup_files = glob.glob("backup_*.json")
    if not backup_files:
        return None
    
    # Sort by filename (which includes timestamp)
    backup_files.sort(reverse=True)
    return backup_files[0]

def main():
    print("🔄 Post-deployment database restore")
    print("=" * 40)
    
    # Find latest backup
    latest_backup = find_latest_backup()
    
    if not latest_backup:
        print("❌ No backup files found!")
        print("Make sure you ran pre_deploy.py before redeploying")
        return
    
    print(f"📁 Found backup: {latest_backup}")
    
    # Restore database
    if restore_database(latest_backup):
        print("🎉 Database restored successfully!")
        print("✅ All your data is back!")
    else:
        print("❌ Database restoration failed!")
        print("Check the error messages above")

if __name__ == '__main__':
    main()
