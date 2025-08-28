"""
Room model for online multiplayer games
"""
from datetime import datetime, timedelta
from app import db
import string
import random

class Room(db.Model):
    """Model for online multiplayer rooms."""
    
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    
    # Players
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Room settings
    max_players = db.Column(db.Integer, default=2)
    allow_spectators = db.Column(db.Boolean, default=True)
    is_private = db.Column(db.Boolean, default=False)
    
    # Game state
    current_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    status = db.Column(db.String(20), default='waiting')  # 'waiting', 'in_game', 'finished'
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    host = db.relationship('User', foreign_keys=[host_id], backref='hosted_rooms')
    guest = db.relationship('User', foreign_keys=[guest_id], backref='joined_rooms')
    current_game = db.relationship('Game', foreign_keys=[current_game_id])
    
    def __repr__(self):
        return f'<Room {self.code}>'
    
    @classmethod
    def generate_code(cls):
        """Generate a unique room code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not cls.query.filter_by(code=code).first():
                return code
    
    @property
    def is_full(self):
        """Check if the room is full."""
        return self.guest_id is not None
    
    @property
    def is_expired(self):
        """Check if the room has expired (no activity for 2 hours)."""
        expiry_time = datetime.utcnow() - timedelta(hours=2)
        return self.last_activity < expiry_time
    
    @property
    def player_count(self):
        """Get the current number of players in the room."""
        count = 1  # Host
        if self.guest_id:
            count += 1
        return count
    
    def add_player(self, user):
        """Add a player to the room."""
        if self.is_full:
            return False
        
        if self.guest_id is None:
            self.guest_id = user.id
            self.update_activity()
            db.session.commit()
            return True
        
        return False
    
    def remove_player(self, user_id):
        """Remove a player from the room."""
        if self.guest_id == user_id:
            self.guest_id = None
            self.update_activity()
            db.session.commit()
            return True
        return False
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def start_game(self, game_id):
        """Start a game in this room."""
        self.current_game_id = game_id
        self.status = 'in_game'
        self.update_activity()
        db.session.commit()
    
    def finish_game(self):
        """Mark the current game as finished."""
        self.status = 'waiting'
        self.update_activity()
        db.session.commit()
    
    def get_players(self):
        """Get list of players in the room."""
        players = [self.host]
        if self.guest:
            players.append(self.guest)
        return players
    
    def to_dict(self):
        """Convert room to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'code': self.code,
            'host_username': self.host.username,
            'guest_username': self.guest.username if self.guest else None,
            'player_count': self.player_count,
            'max_players': self.max_players,
            'status': self.status,
            'allow_spectators': self.allow_spectators,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
