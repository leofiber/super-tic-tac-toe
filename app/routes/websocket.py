"""
WebSocket event handlers for real-time multiplayer functionality.
"""
import random
import string
import json
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from app.models import User
from game.engine import create_board, create_small_board_status, get_available_moves, update_small_board_status, check_big_board_winner, PLAYER_X, PLAYER_O

# Global storage for game rooms
game_rooms = {}

def generate_room_code():
    """Generate a unique 6-character room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in game_rooms:
            return code

def register_socketio_events(socketio):
    """Register all WebSocket event handlers."""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        user_info = "Anonymous" if not current_user.is_authenticated else current_user.username
        print(f"WebSocket connected: {user_info} ({request.sid})")
        emit('connected', {'message': f'Welcome {user_info}!'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        user_info = "Anonymous" if not current_user.is_authenticated else current_user.username
        print(f"WebSocket disconnected: {user_info} ({request.sid})")
        
        # Find and clean up any rooms this user was in
        for room_code, room_data in list(game_rooms.items()):
            if request.sid in [room_data.get('player1_sid'), room_data.get('player2_sid')]:
                # Notify other player about disconnection with flashcard
                emit('player_disconnected', {
                    'message': f'{user_info} disconnected',
                    'username': user_info,
                    'room_code': room_code
                }, room=room_code)
                
                # Mark player as disconnected but keep room alive for rejoin
                if room_data.get('player1_sid') == request.sid:
                    room_data['player1_sid'] = None
                    room_data['player1_disconnected'] = True
                elif room_data.get('player2_sid') == request.sid:
                    room_data['player2_sid'] = None
                    room_data['player2_disconnected'] = True
                
                # Only clean up room if both players are disconnected
                if (not room_data.get('player1_sid') and not room_data.get('player2_sid')):
                    del game_rooms[room_code]
    
    @socketio.on('create_room')
    def handle_create_room():
        """Create a new game room."""
        if not current_user.is_authenticated:
            emit('error', {'message': 'You must be logged in to create a room'})
            return
        
        room_code = generate_room_code()
        
        # Initialize game state
        board = create_board()
        small_status = create_small_board_status()
        
        # Randomly decide who goes first
        starting_player = PLAYER_X if random.choice([True, False]) else PLAYER_O
        
        game_rooms[room_code] = {
            'room_code': room_code,
            'player1_sid': request.sid,
            'player1_username': current_user.username,
            'player1_id': current_user.id,
            'player2_sid': None,
            'player2_username': None,
            'player2_id': None,
            'board': board,
            'small_status': small_status,
            'current_player': starting_player,
            'current_board': None,
            'game_started': False,
            'game_over': False,
            'winner': None,
            'spectators': []
        }
        
        join_room(room_code)
        
        emit('room_created', {
            'room_code': room_code,
            'creator_name': current_user.username,
            'message': f'Room {room_code} created! Share this code with your friend.'
        })
        
        print(f"Room {room_code} created by {current_user.username}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Join an existing game room."""
        room_code = data.get('room_code', '').upper().strip()
        
        if not room_code:
            emit('error', {'message': 'Please enter a room code'})
            return
        
        if room_code not in game_rooms:
            emit('error', {'message': f'Room {room_code} does not exist'})
            return
        
        room = game_rooms[room_code]
        
        # Check if this user was previously in this room (rejoin scenario)
        is_rejoin = False
        player_number = None
        
        if current_user.is_authenticated:
            if room.get('player1_id') == current_user.id:
                is_rejoin = True
                player_number = 1
                room['player1_sid'] = request.sid
                room['player1_disconnected'] = False
            elif room.get('player2_id') == current_user.id:
                is_rejoin = True
                player_number = 2
                room['player2_sid'] = request.sid
                room['player2_disconnected'] = False
        
        # If not rejoining, check if room is full
        if not is_rejoin and room['player1_sid'] and room['player2_sid']:
            emit('error', {'message': f'Room {room_code} is full'})
            return
        
        join_room(room_code)
        
        if is_rejoin:
            # Notify all players in room about rejoin
            emit('player_rejoined', {
                'message': f'{current_user.username} rejoined the game',
                'username': current_user.username,
                'player_number': player_number
            }, room=room_code)
            
            # Send room_joined to all players to update UI
            emit('room_joined', {
                'room_code': room_code,
                'player_number': player_number,
                'player1_name': room['player1_username'],
                'player2_name': room['player2_username'],
                'is_rejoin': True,
                'message': f'Rejoined room {room_code}'
            }, room=room_code)
            
            print(f"Player {current_user.username} rejoined room {room_code}")
        else:
            # Add as player 2 if slot available
            if not room['player2_sid']:
                room['player2_sid'] = request.sid
                room['player2_username'] = current_user.username if current_user.is_authenticated else 'Guest'
                room['player2_id'] = current_user.id if current_user.is_authenticated else None
                player_number = 2
                
                # Notify all players in room about the new player
                emit('room_joined', {
                    'room_code': room_code,
                    'player_number': 2,
                    'player1_name': room['player1_username'],
                    'player2_name': room['player2_username'],
                    'opponent': room['player1_username']
                }, room=room_code)
                
                print(f"Player joined room {room_code}: {room['player1_username']} vs {room['player2_username']}")
            else:
                emit('error', {'message': 'Failed to join room'})
                return
    
    @socketio.on('start_game')
    def handle_start_game(data):
        """Start the game in a room."""
        room_code = data.get('room_code')
        
        if not room_code:
            emit('error', {'message': 'Room code required'})
            return
        
        if room_code not in game_rooms:
            emit('error', {'message': 'Room not found'})
            return
        
        room = game_rooms[room_code]
        
        # Verify both players are present
        if not room['player1_sid'] or not room['player2_sid']:
            emit('error', {'message': 'Both players must be present to start'})
            return
        
        # Start the game
        room['game_started'] = True
        legal_moves = get_available_moves(room['board'], room['small_status'], room['current_board'])
        
        emit('game_started', {
            'room_code': room_code,
            'player1': room['player1_username'],
            'player2': room['player2_username'],
            'current_player': room['current_player'],
            'board': room['board'].tolist(),
            'small_status': room['small_status'].tolist(),
            'current_board': room['current_board'],
            'game_over': room.get('game_over', False),
            'winner': room.get('winner', None),
            'legal_moves': legal_moves
        }, room=room_code)
        
        print(f"Game started in room {room_code}: {room['player1_username']} vs {room['player2_username']}")
    
    @socketio.on('make_move')
    def handle_make_move(data):
        """Handle a player making a move."""
        room_code = data.get('room_code')
        row = data.get('row')
        col = data.get('col')
        
        if not all([room_code, row is not None, col is not None]):
            emit('error', {'message': 'Invalid move data'})
            return
        
        if room_code not in game_rooms:
            emit('error', {'message': 'Room not found'})
            return
        
        room = game_rooms[room_code]
        
        # Verify game is in progress
        if not room['game_started'] or room['game_over']:
            emit('error', {'message': 'Game is not in progress'})
            return
        
        # Determine which player is making the move
        player_number = None
        if request.sid == room['player1_sid']:
            player_number = PLAYER_X
        elif request.sid == room['player2_sid']:
            player_number = PLAYER_O
        else:
            emit('error', {'message': 'You are not a player in this game'})
            return
        
        # Verify it's the player's turn
        if room['current_player'] != player_number:
            emit('error', {'message': 'Not your turn'})
            return
        
        # Verify move is legal
        legal_moves = get_available_moves(room['board'], room['small_status'], room['current_board'])
        if (row, col) not in legal_moves:
            emit('error', {'message': 'Illegal move'})
            return
        
        # Apply the move
        room['board'][row, col] = player_number
        update_small_board_status(room['board'], room['small_status'])
        
        # Check for winner
        winner = check_big_board_winner(room['small_status'])
        if winner != 0:
            room['winner'] = winner
            room['game_over'] = True
        elif len(get_available_moves(room['board'], room['small_status'], room['current_board'])) == 0:
            room['winner'] = 0  # Draw
            room['game_over'] = True
        
        # Determine next board and switch turns
        if not room['game_over']:
            ib, jb = row % 3, col % 3
            if room['small_status'][ib, jb] == 0:
                room['current_board'] = (ib, jb)
            else:
                room['current_board'] = None
            
            # Switch turns
            room['current_player'] = PLAYER_O if player_number == PLAYER_X else PLAYER_X
        
                        # Broadcast move to all in room
        legal_moves = get_available_moves(room['board'], room['small_status'], room['current_board']) if not room['game_over'] else []
        
        move_data = {
            'row': row,
            'col': col,
            'player': player_number,
            'board': room['board'].tolist(),
            'small_status': room['small_status'].tolist(),
            'current_board': room['current_board'],
            'current_player': room['current_player'],
            'game_over': room['game_over'],
            'winner': room['winner'],
            'legal_moves': legal_moves
        }
        
        emit('move_made', move_data, room=room_code)
        
        # Update statistics if game ended
        if room['game_over']:
            update_online_game_stats(room)
            
            game_result = 'Draw' if room['winner'] == 0 else f"Player {room['winner']} wins!"
            emit('game_ended', {
                'winner': room['winner'],
                'message': game_result
            }, room=room_code)
    
    @socketio.on('reset_game')
    def handle_reset_game(data):
        """Reset the game in a room."""
        room_code = data.get('room_code')
        
        if room_code not in game_rooms:
            emit('error', {'message': 'Room not found'})
            return
        
        room = game_rooms[room_code]
        
        # Only players can reset
        if request.sid not in [room['player1_sid'], room['player2_sid']]:
            emit('error', {'message': 'Only players can reset the game'})
            return
        
        # Reset game state
        room['board'] = create_board()
        room['small_status'] = create_small_board_status()
        room['current_player'] = PLAYER_X if random.choice([True, False]) else PLAYER_O
        room['current_board'] = None
        room['game_over'] = False
        room['winner'] = None
        
        # Broadcast reset to room
        legal_moves = get_available_moves(room['board'], room['small_status'], room['current_board'])
        
        emit('game_reset', {
            'board': room['board'].tolist(),
            'small_status': room['small_status'].tolist(),
            'current_player': room['current_player'],
            'current_board': room['current_board'],
            'legal_moves': legal_moves
        }, room=room_code)
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Leave a game room."""
        room_code = data.get('room_code')
        
        if room_code not in game_rooms:
            emit('error', {'message': 'Room not found'})
            return
        
        room = game_rooms[room_code]
        
        # Mark player as disconnected
        if request.sid == room.get('player1_sid'):
            room['player1_sid'] = None
            room['player1_disconnected'] = True
            username = room.get('player1_username', 'Player 1')
        elif request.sid == room.get('player2_sid'):
            room['player2_sid'] = None
            room['player2_disconnected'] = True
            username = room.get('player2_username', 'Player 2')
        else:
            emit('error', {'message': 'You are not in this room'})
            return
        
        leave_room(room_code)
        
        # Notify other players
        emit('player_disconnected', {
            'username': username,
            'room_code': room_code
        }, room=room_code)
        
        # If both players are gone, delete the room
        if not room.get('player1_sid') and not room.get('player2_sid'):
            del game_rooms[room_code]
            print(f"Room {room_code} deleted - no players remaining")
        else:
            # If only one player left, notify the remaining player that room is closing
            emit('room_closing', {'message': 'Host left the room. Room will close shortly.'}, room=room_code)
        
        emit('left_room', {'room_code': room_code})
    
    @socketio.on('kick_player')
    def handle_kick_player(data):
        """Kick a player from the room (host only)."""
        room_code = data.get('room_code')
        
        if room_code not in game_rooms:
            emit('error', {'message': 'Room not found'})
            return
        
        room = game_rooms[room_code]
        
        # Only host (player1) can kick
        if request.sid != room.get('player1_sid'):
            emit('error', {'message': 'Only the host can kick players'})
            return
        
        # Kick player 2
        if room.get('player2_sid'):
            # Send kick notification to player 2
            emit('player_kicked', {
                'message': 'You have been kicked from the room by the host'
            }, room=room['player2_sid'])
            
            # Remove player 2 from room (but allow rejoin)
            room['player2_sid'] = None
            room['player2_disconnected'] = True
            
            # Notify host
            emit('player_kicked', {
                'message': f'Kicked {room.get("player2_username", "Player 2")} from the room'
            })
            
            print(f"Player 2 kicked from room {room_code}")
        else:
            emit('error', {'message': 'No player to kick'})
    
    @socketio.on('ping_room')
    def handle_ping_room(data):
        """Check if a room exists."""
        room_code = data.get('room_code')
        
        if room_code not in game_rooms:
            emit('room_not_found', {'message': 'Room no longer exists'})
        else:
            emit('room_exists', {'room_code': room_code})
    
    def update_online_game_stats(room):
        """Update statistics for completed online game."""
        try:
            from app.routes.game import update_game_stats
            from flask_login import current_user
            
            # Update stats for both players
            for player_key in ['player1', 'player2']:
                player_id = room.get(f'{player_key}_id')
                player_username = room.get(f'{player_key}_username')
                
                if player_id:
                    # For registered users, temporarily set current_user context
                    user = User.query.get(player_id)
                    if user:
                        player_number = PLAYER_X if player_key == 'player1' else PLAYER_O
                        
                        # Convert room winner to player perspective
                        if room['winner'] == player_number:
                            winner_result = 1  # This player won
                        elif room['winner'] == 0:
                            winner_result = 0  # Draw
                        else:
                            winner_result = -1  # This player lost
                        
                        print(f"Updating stats for {player_username} (player {player_number}): winner={room['winner']}, result={winner_result}")
                        
                        # Temporarily update current_user for the update_game_stats call
                        from flask import g
                        original_user = getattr(g, '_login_user', None)
                        g._login_user = user
                        
                        try:
                            update_game_stats('pvp_online', None, winner_result, player_number)
                        finally:
                            # Restore original user context
                            if original_user:
                                g._login_user = original_user
                            else:
                                delattr(g, '_login_user')
            
            # Create a proper game record for online PvP with both players
            if room.get('player1_id') and room.get('player2_id'):
                from app.models import Game
                from datetime import datetime
                import json
                
                game_record = Game(
                    player1_id=room['player1_id'],
                    player2_id=room['player2_id'],
                    game_type='pvp_online',
                    board_state=json.dumps(room['board'].tolist()),
                    small_board_state=json.dumps(room['small_status'].tolist()),
                    winner=room['winner'],
                    finished_at=datetime.now()
                )
                
                from app import db
                db.session.add(game_record)
                db.session.commit()
                print(f"Created game record for online PvP: {room['player1_username']} vs {room['player2_username']}")
            
            print(f"Updated stats for online game in room {room.get('room_code', 'unknown')}")
            
        except Exception as e:
            print(f"Error updating online game stats: {e}")