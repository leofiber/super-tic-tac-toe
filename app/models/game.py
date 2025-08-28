"""
Game and GameMove models for storing game history
"""
from datetime import datetime
from app import db
import json

class Game(db.Model):
    """Model for storing completed games."""
    
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    game_type = db.Column(db.String(20), nullable=False)  # 'pvai', 'pvp_local', 'pvp_online'
    
    # Players
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # X player
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # O player
    ai_difficulty = db.Column(db.String(10), nullable=True)  # 'easy', 'medium', 'hard'
    
    # Game state
    board_state = db.Column(db.Text, nullable=False)  # JSON string of final board
    small_board_state = db.Column(db.Text, nullable=False)  # JSON string of small board status
    winner = db.Column(db.Integer, nullable=True)  # 1 for X, -1 for O, 0 for draw, None for ongoing
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    total_moves = db.Column(db.Integer, default=0)
    
    # Room info for online games
    room_code = db.Column(db.String(10), nullable=True)
    
    # Relationships
    moves = db.relationship('GameMove', backref='game', lazy='dynamic', 
                           cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Game {self.id}: {self.game_type}>'
    
    @property
    def duration(self):
        """Calculate game duration in seconds."""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
    
    @property
    def board_as_list(self):
        """Get board state as a list."""
        return json.loads(self.board_state)
    
    @property
    def small_board_as_list(self):
        """Get small board state as a list."""
        return json.loads(self.small_board_state)
    
    def set_board_state(self, board, small_board):
        """Set board states from numpy arrays."""
        self.board_state = json.dumps(board.tolist())
        self.small_board_state = json.dumps(small_board.tolist())
    
    def start_game(self):
        """Mark the game as started."""
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def finish_game(self, winner):
        """Mark the game as finished with a winner."""
        self.finished_at = datetime.utcnow()
        self.winner = winner
        db.session.commit()
    
    def to_dict(self):
        """Convert game to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'game_type': self.game_type,
            'player1_username': self.player1_user.username if self.player1_user else None,
            'player2_username': self.player2_user.username if self.player2_user else 'AI',
            'ai_difficulty': self.ai_difficulty,
            'winner': self.winner,
            'total_moves': self.total_moves,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }

class GameMove(db.Model):
    """Model for storing individual moves in a game."""
    
    __tablename__ = 'game_moves'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    
    # Move details
    move_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, ...
    player = db.Column(db.Integer, nullable=False)  # 1 for X, -1 for O
    row = db.Column(db.Integer, nullable=False)
    col = db.Column(db.Integer, nullable=False)
    
    # Timing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    think_time = db.Column(db.Float, nullable=True)  # Time taken to make the move (for AI)
    
    def __repr__(self):
        return f'<Move {self.move_number}: ({self.row}, {self.col})>'
    
    def to_dict(self):
        """Convert move to dictionary for JSON serialization."""
        return {
            'move_number': self.move_number,
            'player': self.player,
            'row': self.row,
            'col': self.col,
            'timestamp': self.timestamp.isoformat(),
            'think_time': self.think_time
        }
