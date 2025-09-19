#!/usr/bin/env python3
"""
Database persistence system for Super Tic-Tac-Toe
Prevents data loss during manual redeploys
"""
import os
import json
import pickle
from datetime import datetime
from app import create_app, db
from app.models import User, Game, GameMove, Room

def backup_database():
    """Create a complete database backup."""
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
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'games_played': user.games_played,
                    'games_won': user.games_won,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })
            
            # Backup games
            for game in Game.query.all():
                backup_data['games'].append({
                    'id': game.id,
                    'player1_id': game.player1_id,
                    'player2_id': game.player2_id,
                    'game_type': game.game_type,
                    'ai_difficulty': game.ai_difficulty,
                    'board_state': game.board_state,
                    'small_board_state': game.small_board_state,
                    'winner': game.winner,
                    'finished_at': game.finished_at.isoformat() if game.finished_at else None
                })
            
            # Backup rooms
            for room in Room.query.all():
                backup_data['rooms'].append({
                    'id': room.id,
                    'room_code': room.room_code,
                    'player1_id': room.player1_id,
                    'player2_id': room.player2_id,
                    'is_active': room.is_active,
                    'created_at': room.created_at.isoformat() if room.created_at else None
                })
            
            # Save backup to file
            backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup saved to {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

def restore_database(backup_file):
    """Restore database from backup."""
    print(f"🔄 Restoring database from {backup_file}...")
    
    app = create_app('production')
    with app.app_context():
        try:
            # Read backup file
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Clear existing data
            db.drop_all()
            db.create_all()
            
            # Restore users
            for user_data in backup_data['users']:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    games_played=user_data['games_played'],
                    games_won=user_data['games_won']
                )
                user.password_hash = user_data['password_hash']
                db.session.add(user)
            
            db.session.commit()
            print("✅ Users restored")
            
            # Restore games
            for game_data in backup_data['games']:
                game = Game(
                    player1_id=game_data['player1_id'],
                    player2_id=game_data['player2_id'],
                    game_type=game_data['game_type'],
                    ai_difficulty=game_data['ai_difficulty'],
                    board_state=game_data['board_state'],
                    small_board_state=game_data['small_board_state'],
                    winner=game_data['winner']
                )
                if game_data['finished_at']:
                    game.finished_at = datetime.fromisoformat(game_data['finished_at'])
                db.session.add(game)
            
            db.session.commit()
            print("✅ Games restored")
            
            # Restore rooms
            for room_data in backup_data['rooms']:
                room = Room(
                    room_code=room_data['room_code'],
                    player1_id=room_data['player1_id'],
                    player2_id=room_data['player2_id'],
                    is_active=room_data['is_active']
                )
                if room_data['created_at']:
                    room.created_at = datetime.fromisoformat(room_data['created_at'])
                db.session.add(room)
            
            db.session.commit()
            print("✅ Rooms restored")
            
            print("🎉 Database restoration complete!")
            return True
            
        except Exception as e:
            print(f"❌ Restoration failed: {e}")
            return False

def check_database_persistence():
    """Check if database has existing data and create backup if needed."""
    print("🔍 Checking database persistence...")
    
    app = create_app('production')
    with app.app_context():
        try:
            # Check if we have existing data
            user_count = User.query.count()
            game_count = Game.query.count()
            
            if user_count > 0 or game_count > 0:
                print(f"✅ Database has existing data: {user_count} users, {game_count} games")
                
                # Create backup before any operations
                backup_file = backup_database()
                if backup_file:
                    print(f"💾 Backup created: {backup_file}")
                    return True
                else:
                    print("⚠️ Backup failed, but data exists")
                    return True
            else:
                print("📝 No existing data found - fresh database")
                return False
                
        except Exception as e:
            print(f"⚠️ Database check failed: {e}")
            return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'backup':
            backup_database()
        elif command == 'restore' and len(sys.argv) > 2:
            restore_database(sys.argv[2])
        elif command == 'check':
            check_database_persistence()
        else:
            print("Usage: python db_persistence.py [backup|restore <file>|check]")
    else:
        check_database_persistence()
