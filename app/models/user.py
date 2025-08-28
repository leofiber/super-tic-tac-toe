"""
User model for authentication and statistics
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and game statistics."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Game statistics
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    games_lost = db.Column(db.Integer, default=0)
    games_drawn = db.Column(db.Integer, default=0)
    
    # AI difficulty stats
    easy_ai_wins = db.Column(db.Integer, default=0)
    medium_ai_wins = db.Column(db.Integer, default=0)
    hard_ai_wins = db.Column(db.Integer, default=0)
    
    # PvP stats
    pvp_wins = db.Column(db.Integer, default=0)
    pvp_losses = db.Column(db.Integer, default=0)
    
    # Settings
    preferred_theme = db.Column(db.String(20), default='dark')
    sound_enabled = db.Column(db.Boolean, default=True)
    
    # Relationships
    games_as_player1 = db.relationship('Game', foreign_keys='Game.player1_id', 
                                      backref='player1_user', lazy='dynamic')
    games_as_player2 = db.relationship('Game', foreign_keys='Game.player2_id', 
                                      backref='player2_user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def win_rate(self):
        """Calculate the user's overall win rate."""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100
    
    @property
    def is_guest(self):
        """Check if this is a guest user."""
        return self.username.startswith('Guest_')
    
    def update_last_seen(self):
        """Update the user's last seen timestamp."""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def record_game_result(self, result, opponent_type='ai', difficulty=None):
        """Record the result of a game."""
        self.games_played += 1
        
        if result == 'win':
            self.games_won += 1
            if opponent_type == 'ai' and difficulty:
                if difficulty == 'easy':
                    self.easy_ai_wins += 1
                elif difficulty == 'medium':
                    self.medium_ai_wins += 1
                elif difficulty == 'hard':
                    self.hard_ai_wins += 1
            elif opponent_type == 'player':
                self.pvp_wins += 1
        elif result == 'loss':
            self.games_lost += 1
            if opponent_type == 'player':
                self.pvp_losses += 1
        elif result == 'draw':
            self.games_drawn += 1
        
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'games_drawn': self.games_drawn,
            'win_rate': self.win_rate,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }
