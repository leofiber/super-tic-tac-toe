"""
AI service for different difficulty levels
"""
import random
import time
from game.engine import (
    hard_ai_move, mcts_ai_move, get_available_moves, 
    check_small_board_winner, PLAYER_O, PLAYER_X, SMALL_SIZE
)
from game.advanced_ai import advanced_ai

class AIService:
    """Service for AI opponents with different difficulty levels."""
    
    @staticmethod
    def get_ai_move(board, small_status, current_board, player, difficulty='medium'):
        """Get AI move based on difficulty level."""
        start_time = time.time()
        
        if difficulty == 'easy':
            move = AIService._easy_ai_move(board, small_status, current_board, player)
        elif difficulty == 'medium':
            move = AIService._medium_ai_move(board, small_status, current_board, player)
        elif difficulty == 'hard':
            move = advanced_ai.get_move(board, small_status, current_board, player)
        else:
            # Default to medium
            move = AIService._medium_ai_move(board, small_status, current_board, player)
        
        think_time = time.time() - start_time
        return move, think_time
    
    @staticmethod
    def _easy_ai_move(board, small_status, current_board, player):
        """Easy AI: Random moves with basic winning/blocking."""
        moves = get_available_moves(board, small_status, current_board)
        
        if not moves:
            return None
        
        # 30% chance to make optimal move, 70% random
        if random.random() < 0.3:
            # Check for immediate wins
            for move in moves:
                row, col = move
                bi, bj = row // SMALL_SIZE, col // SMALL_SIZE
                if small_status[bi, bj] == 0:
                    # Simulate move
                    board_copy = board.copy()
                    board_copy[row, col] = player
                    if check_small_board_winner(board_copy, bi, bj) == player:
                        return move
            
            # Check for blocks (prevent opponent from winning small board)
            opponent = -player
            for move in moves:
                row, col = move
                bi, bj = row // SMALL_SIZE, col // SMALL_SIZE
                if small_status[bi, bj] == 0:
                    # Simulate opponent move
                    board_copy = board.copy()
                    board_copy[row, col] = opponent
                    if check_small_board_winner(board_copy, bi, bj) == opponent:
                        return move
        
        # Random move from legal moves
        return random.choice(moves)
    
    @staticmethod
    def _medium_ai_move(board, small_status, current_board, player):
        """Medium AI: MCTS with shorter time limit."""
        # Use a simplified version of MCTS with reduced time
        moves = get_available_moves(board, small_status, current_board)
        
        if not moves:
            return None
        
        # Immediate win check
        for move in moves:
            row, col = move
            board_copy = board.copy()
            small_status_copy = small_status.copy()
            board_copy[row, col] = player
            
            # Check if this move wins a small board
            bi, bj = row // SMALL_SIZE, col // SMALL_SIZE
            if small_status[bi, bj] == 0:
                if check_small_board_winner(board_copy, bi, bj) == player:
                    return move
        
        # Blocking check
        opponent = -player
        for move in moves:
            row, col = move
            board_copy = board.copy()
            board_copy[row, col] = opponent
            
            bi, bj = row // SMALL_SIZE, col // SMALL_SIZE
            if small_status[bi, bj] == 0:
                if check_small_board_winner(board_copy, bi, bj) == opponent:
                    return move
        
        # Use simplified MCTS for remaining moves
        return AIService._simple_mcts(board, small_status, current_board, player, time_limit=2.0)
    
    @staticmethod
    def _simple_mcts(board, small_status, current_board, player, time_limit=2.0):
        """Simplified MCTS implementation."""
        moves = get_available_moves(board, small_status, current_board)
        if not moves:
            return None
        
        wins = {move: 0 for move in moves}
        total_simulations = {move: 0 for move in moves}
        
        start_time = time.time()
        simulations = 0
        max_simulations = 500  # Reduced for medium difficulty
        
        while simulations < max_simulations and (time.time() - start_time) < time_limit:
            # Select random move to try
            move = random.choice(moves)
            
            # Simulate game from this move
            result = AIService._simulate_random_game(board, small_status, current_board, player, move)
            
            total_simulations[move] += 1
            if result == player:
                wins[move] += 1
            
            simulations += 1
        
        # Choose move with best win rate
        best_move = None
        best_rate = -1
        
        for move in moves:
            if total_simulations[move] > 0:
                win_rate = wins[move] / total_simulations[move]
                if win_rate > best_rate:
                    best_rate = win_rate
                    best_move = move
        
        return best_move or random.choice(moves)
    
    @staticmethod
    def _simulate_random_game(board, small_status, current_board, player, first_move):
        """Simulate a random game to completion."""
        from game.engine import update_small_board_status, check_big_board_winner
        
        # Make copies for simulation
        sim_board = board.copy()
        sim_small_status = small_status.copy()
        current_player = player
        current_constraint = current_board
        
        # Make the first move
        row, col = first_move
        sim_board[row, col] = current_player
        update_small_board_status(sim_board, sim_small_status)
        
        # Determine next constraint
        next_board_row, next_board_col = row % SMALL_SIZE, col % SMALL_SIZE
        if sim_small_status[next_board_row, next_board_col] == 0:
            current_constraint = (next_board_row, next_board_col)
        else:
            current_constraint = None
        
        current_player = -current_player
        
        # Continue with random moves
        for _ in range(81):  # Maximum possible moves
            winner = check_big_board_winner(sim_small_status)
            if winner != 0:
                return winner
            
            moves = get_available_moves(sim_board, sim_small_status, current_constraint)
            if not moves:
                return 0  # Draw
            
            # Random move
            row, col = random.choice(moves)
            sim_board[row, col] = current_player
            update_small_board_status(sim_board, sim_small_status)
            
            # Update constraint
            next_board_row, next_board_col = row % SMALL_SIZE, col % SMALL_SIZE
            if sim_small_status[next_board_row, next_board_col] == 0:
                current_constraint = (next_board_row, next_board_col)
            else:
                current_constraint = None
            
            current_player = -current_player
        
        return 0  # Draw if game doesn't finish
