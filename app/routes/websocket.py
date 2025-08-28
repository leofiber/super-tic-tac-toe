"""
WebSocket events for real-time multiplayer
"""
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.models import Room, Game

def register_socketio_events(socketio):
    """Register all WebSocket event handlers."""
    
    @socketio.on('connect')
    def on_connect():
        """Handle client connection."""
        if current_user.is_authenticated:
            emit('connected', {'message': f'Welcome, {current_user.username}!'})
        else:
            emit('connected', {'message': 'Connected as guest'})
    
    @socketio.on('disconnect')
    def on_disconnect():
        """Handle client disconnection."""
        print(f'User {current_user.username if current_user.is_authenticated else "Guest"} disconnected')
    
    @socketio.on('join_game_room')
    def on_join_game_room(data):
        """Join a game room for real-time updates."""
        room_code = data.get('room_code')
        if room_code:
            join_room(room_code)
            emit('joined_room', {'room_code': room_code})
            # Notify others in the room
            emit('player_joined', {
                'username': current_user.username if current_user.is_authenticated else 'Guest'
            }, room=room_code, include_self=False)
    
    @socketio.on('leave_game_room')
    def on_leave_game_room(data):
        """Leave a game room."""
        room_code = data.get('room_code')
        if room_code:
            leave_room(room_code)
            emit('left_room', {'room_code': room_code})
            # Notify others in the room
            emit('player_left', {
                'username': current_user.username if current_user.is_authenticated else 'Guest'
            }, room=room_code, include_self=False)
    
    @socketio.on('game_move')
    def on_game_move(data):
        """Handle real-time game moves."""
        room_code = data.get('room_code')
        move_data = data.get('move')
        
        if room_code and move_data:
            # Broadcast move to all players in the room
            emit('move_made', {
                'player': current_user.username if current_user.is_authenticated else 'Guest',
                'move': move_data
            }, room=room_code, include_self=False)
    
    @socketio.on('chat_message')
    def on_chat_message(data):
        """Handle in-game chat messages."""
        room_code = data.get('room_code')
        message = data.get('message', '').strip()
        
        if room_code and message and len(message) <= 200:
            emit('chat_message', {
                'username': current_user.username if current_user.is_authenticated else 'Guest',
                'message': message,
                'timestamp': data.get('timestamp')
            }, room=room_code)
    
    @socketio.on('game_state_update')
    def on_game_state_update(data):
        """Broadcast game state updates."""
        room_code = data.get('room_code')
        game_state = data.get('game_state')
        
        if room_code and game_state:
            emit('game_updated', game_state, room=room_code, include_self=False)
