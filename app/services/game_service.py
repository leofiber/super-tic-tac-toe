"""
Game service for managing game logic and state
"""
import json
from datetime import datetime
from app import db
from app.models import Game, GameMove, User
from game.engine import (
    create_board, create_small_board_status, get_available_moves,
    update_small_board_status, check_big_board_winner, PLAYER_X, PLAYER_O, SMALL_SIZE
)

class GameService:
    """Service for managing game operations."""
    
    def __init__(self):
        self.active_games = {}  # In-memory storage for active games
    
    def create_game(self, game_type, player1_id=None, player2_id=None, ai_difficulty=None, room_code=None):
        """Create a new game instance."""
        game = Game(
            game_type=game_type,
            player1_id=player1_id,
            player2_id=player2_id,
            ai_difficulty=ai_difficulty,
            room_code=room_code
        )
        
        # Initialize game state
        board = create_board()
        small_status = create_small_board_status()
        
        game.set_board_state(board, small_status)
        
        db.session.add(game)
        db.session.commit()
        
        # Store in active games
        self.active_games[game.id] = {
            'board': board,
            'small_status': small_status,
            'current_player': PLAYER_X,
            'current_board': None,
            'move_count': 0
        }
        
        return game
    
    def get_game_state(self, game_id):
        """Get current game state."""
        if game_id not in self.active_games:
            # Try to load from database
            game = Game.query.get(game_id)
            if not game or game.winner is not None:
                return None
            
            # Restore state from database
            self.active_games[game_id] = {
                'board': json.loads(game.board_state),
                'small_status': json.loads(game.small_board_state),
                'current_player': PLAYER_X if game.total_moves % 2 == 0 else PLAYER_O,
                'current_board': None,  # TODO: Calculate from last move
                'move_count': game.total_moves
            }
        
        state = self.active_games[game_id]
        legal_moves = get_available_moves(
            state['board'], 
            state['small_status'], 
            state['current_board']
        )
        
        return {
            'board': state['board'].tolist() if hasattr(state['board'], 'tolist') else state['board'],
            'small_status': state['small_status'].tolist() if hasattr(state['small_status'], 'tolist') else state['small_status'],
            'current_player': state['current_player'],
            'current_board': state['current_board'],
            'legal_moves': legal_moves,
            'move_count': state['move_count']
        }
    
    def make_move(self, game_id, row, col, player):
        """Make a move in the game."""
        if game_id not in self.active_games:
            return {'error': 'Game not found'}
        
        state = self.active_games[game_id]
        
        # Validate turn
        if state['current_player'] != player:
            return {'error': 'Not your turn'}
        
        # Validate move legality
        legal_moves = get_available_moves(
            state['board'], 
            state['small_status'], 
            state['current_board']
        )
        
        if (row, col) not in legal_moves:
            return {'error': 'Illegal move'}
        
        # Apply move
        state['board'][row, col] = player
        update_small_board_status(state['board'], state['small_status'])
        
        # Determine next board
        next_board_row, next_board_col = row % SMALL_SIZE, col % SMALL_SIZE
        if state['small_status'][next_board_row, next_board_col] == 0:
            state['current_board'] = (next_board_row, next_board_col)
        else:
            state['current_board'] = None
        
        # Switch players
        state['current_player'] = -player
        state['move_count'] += 1
        
        # Record move in database
        self._record_move(game_id, state['move_count'], player, row, col)
        
        # Check for winner
        winner = check_big_board_winner(state['small_status'])
        
        if winner != 0 or self._is_board_full(state['board']):
            self._finish_game(game_id, winner)
        else:
            # Update game state in database
            self._update_game_state(game_id, state)
        
        return {
            'success': True,
            'winner': winner if winner != 0 else None,
            'game_state': self.get_game_state(game_id)
        }
    
    def _record_move(self, game_id, move_number, player, row, col, think_time=None):
        """Record a move in the database."""
        move = GameMove(
            game_id=game_id,
            move_number=move_number,
            player=player,
            row=row,
            col=col,
            think_time=think_time
        )
        db.session.add(move)
        db.session.commit()
    
    def _update_game_state(self, game_id, state):
        """Update game state in database."""
        game = Game.query.get(game_id)
        if game:
            game.set_board_state(state['board'], state['small_status'])
            game.total_moves = state['move_count']
            db.session.commit()
    
    def _finish_game(self, game_id, winner):
        """Finish a game and update statistics."""
        game = Game.query.get(game_id)
        if game:
            game.finish_game(winner)
            
            # Update player statistics
            if game.player1_id:
                player1 = User.query.get(game.player1_id)
                if winner == PLAYER_X:
                    player1.record_game_result('win', 'ai' if game.game_type == 'pvai' else 'player', game.ai_difficulty)
                elif winner == PLAYER_O:
                    player1.record_game_result('loss', 'ai' if game.game_type == 'pvai' else 'player', game.ai_difficulty)
                else:
                    player1.record_game_result('draw', 'ai' if game.game_type == 'pvai' else 'player', game.ai_difficulty)
            
            if game.player2_id:
                player2 = User.query.get(game.player2_id)
                if winner == PLAYER_O:
                    player2.record_game_result('win', 'player')
                elif winner == PLAYER_X:
                    player2.record_game_result('loss', 'player')
                else:
                    player2.record_game_result('draw', 'player')
        
        # Remove from active games
        if game_id in self.active_games:
            del self.active_games[game_id]
    
    def _is_board_full(self, board):
        """Check if the board is completely full."""
        return not (board == 0).any()
    
    def abandon_game(self, game_id, abandoning_player):
        """Handle a player abandoning the game."""
        if game_id in self.active_games:
            # The other player wins
            winner = -abandoning_player
            self._finish_game(game_id, winner)
            return True
        return False
    
    def get_game_history(self, user_id, limit=10):
        """Get recent games for a user."""
        games = Game.query.filter(
            (Game.player1_id == user_id) | (Game.player2_id == user_id)
        ).filter(
            Game.winner.isnot(None)
        ).order_by(
            Game.finished_at.desc()
        ).limit(limit).all()
        
        return [game.to_dict() for game in games]
