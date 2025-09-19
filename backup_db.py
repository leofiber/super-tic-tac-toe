#!/usr/bin/env python3
"""
Database backup script for Super Tic-Tac-Toe
"""
import os
import json
from datetime import datetime
from app import create_app, db
from app.models import User, Game, GameMove, Room

def backup_database():
    """Backup database to JSON file."""
    print("💾 Creating database backup...")
    
    app = create_app('production')
    with app.app_context():
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'users': [],
                'games': [],
                'rooms': []
            }
            
            # Backup users
            for user in User.query.all():
                backup_data['users'].append({
                    'username': user.username,
                    'email': user.email,
                    'games_played': user.games_played,
                    'games_won': user.games_won
                })
            
            # Backup games
            for game in Game.query.all():
                backup_data['games'].append({
                    'id': game.id,
                    'player1_id': game.player1_id,
                    'player2_id': game.player2_id,
                    'game_type': game.game_type,
                    'winner': game.winner,
                    'finished_at': game.finished_at.isoformat() if game.finished_at else None
                })
            
            # Save backup
            backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup saved to {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

if __name__ == '__main__':
    backup_database()
