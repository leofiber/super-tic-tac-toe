"""
Game routes for different game modes
"""
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from flask_login import login_required, current_user
from app.models import Game, Room, User
from app.services import GameService, AIService
from app import db
import json
import random
import time

# Import the working game engine
from game.engine import (
    create_board, create_small_board_status, get_available_moves,
    update_small_board_status, check_big_board_winner, hard_ai_move,
    mcts_ai_move, PLAYER_X, PLAYER_O, SMALL_SIZE
)
# from game.advanced_ai import advanced_ai  # Reverted to original working AI

game_bp = Blueprint('game', __name__)
game_service = GameService()

# Simple in-memory game storage for testing
game_sessions = {}

def init_guest_stats():
    """Initialize guest stats in session if not exists."""
    if 'game_stats' not in session:
        session['game_stats'] = {
            'ai_stats': {
                'easy': {'wins': 0, 'draws': 0, 'total_games': 0},
                'medium': {'wins': 0, 'draws': 0, 'total_games': 0}, 
                'hard': {'wins': 0, 'draws': 0, 'total_games': 0}
            },
            'pvp_stats': {'wins': 0, 'draws': 0, 'total_games': 0},
            'recent_games': []  # Track recent games for guests
        }
        session.permanent = True  # Make session persistent

def update_game_stats(game_type, difficulty, winner, player_number=1, board_state=None, small_board_state=None):
    """Update game statistics for both guest and registered users."""
    
    # For guests: update session stats
    if not current_user or not current_user.is_authenticated:
        init_guest_stats()
        stats = session['game_stats']
        
        if game_type == 'pvai':
            ai_stat = stats['ai_stats'][difficulty]
            ai_stat['total_games'] += 1
            if winner == player_number:  # Player won
                ai_stat['wins'] += 1
            elif winner == 0:  # Draw
                ai_stat['draws'] += 1
            
            # Add to recent games (keep only last 5)
            from datetime import datetime
            result = 'Won' if winner == player_number else 'Draw' if winner == 0 else 'Lost'
            recent_game = {
                'game_type': 'pvai',
                'ai_difficulty': difficulty,
                'result': result,
                'finished_at': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            stats['recent_games'].insert(0, recent_game)  # Add to front
            stats['recent_games'] = stats['recent_games'][:5]  # Keep only last 5
        elif game_type in ['pvp_local', 'pvp_online']:
            pvp_stat = stats['pvp_stats']
            pvp_stat['total_games'] += 1
            if winner == 1:  # Player 1 (logged-in user) won
                pvp_stat['wins'] += 1
            elif winner == 0:  # Draw
                pvp_stat['draws'] += 1
            # If winner == -1, it's a loss (Player 2 won)
            
            # Add to recent games
            from datetime import datetime
            result = 'Win' if winner == 1 else 'Draw' if winner == 0 else 'Loss'
            mode = 'Local PvP' if game_type == 'pvp_local' else 'Online PvP'
            recent_game = {
                'mode': mode,
                'opponent': 'Player',  # For guest users, we don't have opponent username
                'result': result,
                'finished_at': datetime.now().strftime('%H:%M')
            }
            stats['recent_games'].insert(0, recent_game)  # Add to front
            stats['recent_games'] = stats['recent_games'][:5]  # Keep only last 5
        
        session['game_stats'] = stats  # Ensure session is updated
        
    else:
        # For registered users: save to database
        from datetime import datetime
        import json
        
        # Provide default board states if not given
        if board_state is None:
            board_state = json.dumps([[0 for _ in range(9)] for _ in range(9)])  # Empty 9x9 board
        if small_board_state is None:
            small_board_state = json.dumps([[0 for _ in range(3)] for _ in range(3)])  # Empty 3x3 status
        
        game_record = Game(
            player1_id=current_user.id,
            game_type=game_type,
            ai_difficulty=difficulty if game_type == 'pvai' else None,
            board_state=board_state,
            small_board_state=small_board_state,
            winner=winner,
            finished_at=datetime.now()
        )
        db.session.add(game_record)
        
        # Also update user statistics by querying fresh from database
        from app.models import User
        user = User.query.get(current_user.id)
        user.games_played += 1
        
        if winner == player_number:  # Player won
            user.games_won += 1
            # Update AI difficulty specific wins
            if game_type == 'pvai':
                if difficulty == 'easy':
                    user.easy_ai_wins += 1
                elif difficulty == 'medium':
                    user.medium_ai_wins += 1
                elif difficulty == 'hard':
                    user.hard_ai_wins += 1
            elif game_type in ['pvp_local', 'pvp_online']:
                user.pvp_wins += 1
        elif winner == 0:  # Draw
            user.games_drawn += 1
        else:  # Player lost
            user.games_lost += 1
            if game_type in ['pvp_local', 'pvp_online']:
                user.pvp_losses += 1
        
        db.session.commit()

def get_user_stats():
    """Get comprehensive stats for current user (guest or registered)."""
    if not current_user or not current_user.is_authenticated:
        # Guest user: get from session
        init_guest_stats()
        stats = session.get('game_stats', {
            'ai_stats': {
                'easy': {'wins': 0, 'draws': 0, 'total_games': 0},
                'medium': {'wins': 0, 'draws': 0, 'total_games': 0}, 
                'hard': {'wins': 0, 'draws': 0, 'total_games': 0}
            },
            'pvp_stats': {'wins': 0, 'draws': 0, 'total_games': 0},
            'recent_games': []
        })
        
        # Calculate totals including PvP
        ai_total_games = sum(ai['total_games'] for ai in stats['ai_stats'].values())
        ai_total_wins = sum(ai['wins'] for ai in stats['ai_stats'].values())
        ai_total_draws = sum(ai['draws'] for ai in stats['ai_stats'].values())
        
        pvp_total_games = stats['pvp_stats']['total_games']
        pvp_total_wins = stats['pvp_stats']['wins']
        pvp_total_draws = stats['pvp_stats']['draws']
        
        total_games = ai_total_games + pvp_total_games
        total_wins = ai_total_wins + pvp_total_wins
        total_draws = ai_total_draws + pvp_total_draws
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        return {
            'total_games': total_games,
            'victories': total_wins,
            'draws': total_draws,
            'win_rate': round(win_rate, 1),
            'ai_stats': stats['ai_stats'],
            'pvp_stats': stats['pvp_stats'],
            'recent_games': stats.get('recent_games', [])
        }
    else:
        # Registered user: query database
        user_games = Game.query.filter(
            (Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)
        ).filter(Game.winner.isnot(None)).all()  # Only finished games
        
        total_games = len(user_games)
        victories = sum(1 for g in user_games if 
                       (g.player1_id == current_user.id and g.winner == 1) or 
                       (g.player2_id == current_user.id and g.winner == -1))
        draws = sum(1 for g in user_games if g.winner == 0)
        win_rate = (victories / total_games * 100) if total_games > 0 else 0
        
        # AI stats breakdown
        ai_stats = {'easy': {'wins': 0, 'draws': 0, 'total_games': 0},
                   'medium': {'wins': 0, 'draws': 0, 'total_games': 0},
                   'hard': {'wins': 0, 'draws': 0, 'total_games': 0}}
        
        for game in user_games:
            if game.game_type == 'pvai' and game.ai_difficulty:
                difficulty = game.ai_difficulty
                ai_stats[difficulty]['total_games'] += 1
                if (game.player1_id == current_user.id and game.winner == 1):
                    ai_stats[difficulty]['wins'] += 1
                elif game.winner == 0:
                    ai_stats[difficulty]['draws'] += 1
        
        # PvP stats breakdown (separate local and online)
        pvp_local_games = [g for g in user_games if g.game_type == 'pvp_local']
        pvp_online_games = [g for g in user_games if g.game_type == 'pvp_online']
        all_pvp_games = pvp_local_games + pvp_online_games
        
        pvp_local_stats = {
            'wins': sum(1 for g in pvp_local_games if 
                       (g.player1_id == current_user.id and g.winner == 1) or 
                       (g.player2_id == current_user.id and g.winner == -1)),
            'draws': sum(1 for g in pvp_local_games if g.winner == 0),
            'total_games': len(pvp_local_games)
        }
        
        pvp_online_stats = {
            'wins': sum(1 for g in pvp_online_games if 
                       (g.player1_id == current_user.id and g.winner == 1) or 
                       (g.player2_id == current_user.id and g.winner == -1)),
            'draws': sum(1 for g in pvp_online_games if g.winner == 0),
            'total_games': len(pvp_online_games)
        }
        
        pvp_stats = {
            'wins': sum(1 for g in all_pvp_games if 
                       (g.player1_id == current_user.id and g.winner == 1) or 
                       (g.player2_id == current_user.id and g.winner == -1)),
            'draws': sum(1 for g in all_pvp_games if g.winner == 0),
            'total_games': len(all_pvp_games)
        }
        
        return {
            'total_games': total_games,
            'victories': victories, 
            'draws': draws,
            'win_rate': round(win_rate, 1),
            'ai_stats': ai_stats,
            'pvp_stats': pvp_stats,
            'pvp_local_stats': pvp_local_stats,
            'pvp_online_stats': pvp_online_stats
        }

def init_game_session(session_id, difficulty='medium'):
    """Initialize a new game session using the proven engine."""
    import random
    
    # Randomly decide who goes first
    player_starts_first = random.choice([True, False])
    starting_player = PLAYER_X if player_starts_first else PLAYER_O
    
    game_sessions[session_id] = {
        'board': create_board(),
        'small_status': create_small_board_status(),
        'player': starting_player,
        'current_board': None,
        'difficulty': difficulty,
        'game_over': False,
        'winner': None,
        'player_starts_first': player_starts_first  # Track if human player goes first
    }
    return game_sessions[session_id]

@game_bp.route('/simple/<difficulty>')
def simple_game(difficulty='medium'):
    """Simple working game using proven engine."""
    if difficulty not in ['easy', 'medium', 'hard']:
        difficulty = 'medium'
    
    # Initialize guest stats to prevent template errors
    init_guest_stats()
    
    # Create unique session ID
    session_id = f"game_{int(time.time() * 1000)}"
    init_game_session(session_id, difficulty)
    
    return render_template('game/simple_pvai.html', 
                         session_id=session_id, 
                         difficulty=difficulty)

@game_bp.route('/pvai')
@game_bp.route('/pvai/<difficulty>')
@login_required
def pvai(difficulty='medium'):
    """Player vs AI game."""
    if difficulty not in ['easy', 'medium', 'hard']:
        difficulty = 'medium'
    
    # Create new AI game
    game = game_service.create_game(
        game_type='pvai',
        player1_id=current_user.id,
        ai_difficulty=difficulty
    )
    
    return render_template('game/pvai.html', 
                         game_id=game.id, 
                         difficulty=difficulty)

@game_bp.route('/pvp/local')
@login_required
def pvp_local():
    """Local Player vs Player game."""
    # Create new local PvP game
    game = game_service.create_game(
        game_type='pvp_local',
        player1_id=current_user.id
    )
    
    return render_template('game/pvp_local.html', game_id=game.id)

@game_bp.route('/pvp/online')
@login_required
def pvp_online():
    """Online PvP lobby."""
    # Get available rooms
    available_rooms = Room.query.filter_by(status='waiting').filter(
        Room.guest_id.is_(None)
    ).order_by(Room.created_at.desc()).limit(10).all()
    
    return render_template('game/pvp_online.html', rooms=available_rooms)

@game_bp.route('/room/create', methods=['POST'])
@login_required
def create_room():
    """Create a new game room."""
    is_private = request.form.get('private') == 'on'
    allow_spectators = request.form.get('spectators') != 'off'
    
    room = Room(
        code=Room.generate_code(),
        host_id=current_user.id,
        is_private=is_private,
        allow_spectators=allow_spectators
    )
    
    db.session.add(room)
    db.session.commit()
    
    flash(f'Room created! Room code: {room.code}', 'success')
    return redirect(url_for('game.room', code=room.code))

@game_bp.route('/room/join', methods=['POST'])
@login_required
def join_room():
    """Join an existing room."""
    room_code = request.form.get('room_code', '').upper().strip()
    
    if not room_code:
        flash('Please enter a room code.', 'error')
        return redirect(url_for('game.pvp_online'))
    
    room = Room.query.filter_by(code=room_code).first()
    
    if not room:
        flash('Room not found.', 'error')
        return redirect(url_for('game.pvp_online'))
    
    if room.is_full:
        flash('Room is full.', 'error')
        return redirect(url_for('game.pvp_online'))
    
    if room.add_player(current_user):
        flash(f'Joined room {room_code}!', 'success')
        return redirect(url_for('game.room', code=room_code))
    else:
        flash('Could not join room.', 'error')
        return redirect(url_for('game.pvp_online'))

@game_bp.route('/room/<code>')
@login_required
def room(code):
    """Game room for online PvP."""
    room = Room.query.filter_by(code=code).first_or_404()
    
    # Check if user is allowed in this room
    if current_user.id not in [room.host_id, room.guest_id]:
        if not room.allow_spectators:
            flash('This room does not allow spectators.', 'error')
            return redirect(url_for('game.pvp_online'))
    
    # Start game if room is full and no game is active
    if room.is_full and room.status == 'waiting':
        game = game_service.create_game(
            game_type='pvp_online',
            player1_id=room.host_id,
            player2_id=room.guest_id,
            room_code=room.code
        )
        room.start_game(game.id)
    
    return render_template('game/room.html', room=room)

# API Routes for game interactions
@game_bp.route('/api/state/<int:game_id>')
@login_required
def get_game_state(game_id):
    """Get current game state."""
    state = game_service.get_game_state(game_id)
    if not state:
        return jsonify({'error': 'Game not found'}), 404
    
    return jsonify(state)

@game_bp.route('/api/move/<int:game_id>', methods=['POST'])
@login_required
def make_move(game_id):
    """Make a player move."""
    data = request.get_json()
    row = data.get('row')
    col = data.get('col')
    
    if row is None or col is None:
        return jsonify({'error': 'Invalid move data'}), 400
    
    # Make the move
    result = game_service.make_move(game_id, row, col, 1)  # Player X
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result)

@game_bp.route('/api/ai_move/<int:game_id>', methods=['POST'])
@login_required
def ai_move(game_id):
    """Get AI move."""
    game = Game.query.get_or_404(game_id)
    
    if game.game_type != 'pvai':
        return jsonify({'error': 'Not an AI game'}), 400
    
    state = game_service.get_game_state(game_id)
    if not state:
        return jsonify({'error': 'Game not found'}), 404
    
    # Get AI move
    move, think_time = AIService.get_ai_move(
        state['board'], 
        state['small_status'], 
        state['current_board'], 
        -1,  # Player O (AI)
        game.ai_difficulty
    )
    
    if not move:
        return jsonify({'error': 'No valid moves'}), 400
    
    # Apply AI move
    result = game_service.make_move(game_id, move[0], move[1], -1)
    
    if 'error' in result:
        return jsonify(result), 400
    
    # Add think time to response
    result['ai_think_time'] = think_time
    result['ai_move'] = {'row': move[0], 'col': move[1]}
    
    return jsonify(result)

@game_bp.route('/api/reset/<int:game_id>', methods=['POST'])
@login_required
def reset_game(game_id):
    """Reset/restart a game."""
    old_game = Game.query.get_or_404(game_id)
    
    # Create new game with same settings
    new_game = game_service.create_game(
        game_type=old_game.game_type,
        player1_id=old_game.player1_id,
        player2_id=old_game.player2_id,
        ai_difficulty=old_game.ai_difficulty,
        room_code=old_game.room_code
    )
    
    return jsonify({
        'success': True,
        'new_game_id': new_game.id,
        'game_state': game_service.get_game_state(new_game.id)
    })

# ===== SIMPLE GAME API ENDPOINTS (Using proven engine) =====

@game_bp.route('/api/state/<session_id>')
def get_simple_game_state(session_id):
    """Get current game state for simple game."""
    if session_id not in game_sessions:
        return jsonify({'error': 'Game not found'}), 404
    
    game = game_sessions[session_id]
    
    # Double-check if game should be over (in case we missed it)
    if not game['game_over']:
        current_winner = check_big_board_winner(game['small_status'])
        if current_winner != 0:
            game['winner'] = current_winner
            game['game_over'] = True
            import json
            board_json = json.dumps(game['board'].tolist())
            small_board_json = json.dumps(game['small_status'].tolist())
            update_game_stats('pvai', game['difficulty'], game['winner'], 1, board_json, small_board_json)
    
    legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board']) if not game['game_over'] else []
    
    return jsonify({
        'board': game['board'].tolist(),
        'small_status': game['small_status'].tolist(),
        'current_board': game['current_board'],
        'legal_moves': legal_moves,
        'current_player': game['player'],
        'player': game['player'],  # For backwards compatibility
        'winner': game['winner'],
        'game_over': game['game_over'],
        'player_starts_first': game.get('player_starts_first', True)
    })

@game_bp.route('/api/move/<session_id>', methods=['POST'])
def make_simple_move(session_id):
    """Make a player move in simple game."""
    if session_id not in game_sessions:
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        data = request.get_json()
        row = data.get('row')
        col = data.get('col')
        
        game = game_sessions[session_id]
        
        # Check if game is over
        if game['game_over']:
            return jsonify({'error': 'Game is already finished'}), 400
            
        # Check if it's player's turn (this should be handled by frontend, but just in case)
        if game['player'] != PLAYER_X:
            return jsonify({'error': 'Invalid turn state'}), 400
        
        # Double-check if game should be over (in case we missed it)
        current_winner = check_big_board_winner(game['small_status'])
        if current_winner != 0:
            game['winner'] = current_winner
            game['game_over'] = True
            import json
            board_json = json.dumps(game['board'].tolist())
            small_board_json = json.dumps(game['small_status'].tolist())
            update_game_stats('pvai', game['difficulty'], game['winner'], 1, board_json, small_board_json)
            return jsonify({
                'board': game['board'].tolist(),
                'small_status': game['small_status'].tolist(), 
                'current_board': game['current_board'],
                'legal_moves': [],
                'winner': current_winner,
                'game_over': True
            })
        
        # Check if move is legal
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        if (row, col) not in legal_moves:
            return jsonify({'error': 'Illegal move'}), 400
        
        # Apply move
        game['board'][row, col] = PLAYER_X
        update_small_board_status(game['board'], game['small_status'])
        
        # Check for winner
        winner = check_big_board_winner(game['small_status'])
        if winner != 0:  # Someone actually won
            game['winner'] = winner
            game['game_over'] = True
        elif len(get_available_moves(game['board'], game['small_status'], game['current_board'])) == 0:
            # No winner but no moves left = draw
            game['winner'] = 0
            game['game_over'] = True
        
        # Only update stats when game actually ends
        if game['game_over']:
            import json
            board_json = json.dumps(game['board'].tolist())
            small_board_json = json.dumps(game['small_status'].tolist())
            update_game_stats('pvai', game['difficulty'], game['winner'], 1, board_json, small_board_json)
        
        # Determine next board (only if game isn't over)
        if not game['game_over']:
            ib, jb = row % SMALL_SIZE, col % SMALL_SIZE
            if game['small_status'][ib, jb] == 0:
                game['current_board'] = (ib, jb)
            else:
                game['current_board'] = None
            
            # Switch to AI turn
            game['player'] = PLAYER_O
        
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        
        return jsonify({
            'board': game['board'].tolist(),
            'small_status': game['small_status'].tolist(),
            'current_board': game['current_board'],
            'legal_moves': legal_moves,
            'winner': winner,
            'game_over': game['game_over']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@game_bp.route('/api/ai_move/<session_id>', methods=['POST'])
def make_simple_ai_move(session_id):
    """Make an AI move in simple game."""
    if session_id not in game_sessions:
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        game = game_sessions[session_id]
        
        # Check if it's AI's turn
        if game['player'] != PLAYER_O or game['game_over']:
            return jsonify({'error': 'Not AI turn'}), 400
        
        # Get AI move based on difficulty
        difficulty = game['difficulty']
        if difficulty == 'easy':
            # Easy: Random move
            legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
            move = random.choice(legal_moves) if legal_moves else None
        elif difficulty == 'medium':
            # Medium: MCTS
            move = mcts_ai_move(game['board'], game['small_status'], game['current_board'], PLAYER_O)
        else:  # hard
            # Hard: Use the original proven hard AI (it was working fine!)
            move = hard_ai_move(game['board'], game['small_status'], game['current_board'], PLAYER_O)
        
        if not move:
            return jsonify({'error': 'No moves available'}), 400
        
        row, col = move
        
        # Apply AI move
        game['board'][row, col] = PLAYER_O
        update_small_board_status(game['board'], game['small_status'])
        
        # Check for winner
        winner = check_big_board_winner(game['small_status'])
        if winner != 0:  # Someone actually won
            game['winner'] = winner
            game['game_over'] = True
        elif len(get_available_moves(game['board'], game['small_status'], game['current_board'])) == 0:
            # No winner but no moves left = draw
            game['winner'] = 0
            game['game_over'] = True
        
        # Only update stats when game actually ends
        if game['game_over']:
            import json
            board_json = json.dumps(game['board'].tolist())
            small_board_json = json.dumps(game['small_status'].tolist())
            update_game_stats('pvai', game['difficulty'], game['winner'], 1, board_json, small_board_json)
        
        # Determine next board (only if game isn't over)
        if not game['game_over']:
            ib, jb = row % SMALL_SIZE, col % SMALL_SIZE
            if game['small_status'][ib, jb] == 0:
                game['current_board'] = (ib, jb)
            else:
                game['current_board'] = None
            
            # Switch back to player
            game['player'] = PLAYER_X
        
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        
        return jsonify({
            'move': {'row': row, 'col': col},
            'board': game['board'].tolist(),
            'small_status': game['small_status'].tolist(),
            'current_board': game['current_board'],
            'legal_moves': legal_moves,
            'winner': winner,
            'game_over': game['game_over']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@game_bp.route('/api/reset/<session_id>', methods=['POST'])
def reset_simple_game(session_id):
    """Reset/restart simple game."""
    try:
        if session_id in game_sessions:
            difficulty = game_sessions[session_id]['difficulty']
        else:
            difficulty = 'medium'
        
        # Reinitialize game (this will randomize starting player)
        game = init_game_session(session_id, difficulty)
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        
        return jsonify({
            'board': game['board'].tolist(),
            'small_status': game['small_status'].tolist(),
            'current_board': game['current_board'],
            'legal_moves': legal_moves,
            'current_player': game['player'],
            'player': game['player'],
            'winner': None,
            'game_over': False,
            'player_starts_first': game.get('player_starts_first', True)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PvP Local Game Routes ====================

@game_bp.route('/api/pvp_state/<int:game_id>')
def get_pvp_game_state(game_id):
    """Get current state of a PvP game."""
    session_id = f"pvp_game_{game_id}"
    
    if session_id not in game_sessions:
        # Initialize new PvP game
        board = create_board()
        small_status = create_small_board_status()
        current_board = None
        legal_moves = get_available_moves(board, small_status, current_board)
        
        # Randomly decide if account owner is Player 1 or Player 2
        import random
        account_owner_is_player1 = random.choice([True, False])
        starting_player = PLAYER_X if random.choice([True, False]) else PLAYER_O
        
        game_sessions[session_id] = {
            'board': board,
            'small_status': small_status,
            'current_board': current_board,
            'legal_moves': legal_moves,
            'winner': None,
            'game_over': False,
            'current_player': starting_player,
            'account_owner_is_player1': account_owner_is_player1  # Track who the account owner is
        }
    
    game = game_sessions[session_id]
    return jsonify({
        'board': game['board'].tolist(),
        'small_status': game['small_status'].tolist(),
        'current_board': game['current_board'],
        'legal_moves': game['legal_moves'],
        'winner': game['winner'],
        'game_over': game['game_over'],
        'current_player': game['current_player'],
        'account_owner_is_player1': game.get('account_owner_is_player1', True)
    })

@game_bp.route('/api/pvp_move/<int:game_id>', methods=['POST'])
def make_pvp_move(game_id):
    """Make a move in PvP game - using EXACT same logic as working AI games."""
    session_id = f"pvp_game_{game_id}"
    if session_id not in game_sessions:
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        data = request.get_json()
        row = data.get('row')
        col = data.get('col')
        player = data.get('player')
        
        game = game_sessions[session_id]
        
        # Check if game is over
        if game['game_over']:
            return jsonify({'error': 'Game is already finished'}), 400
        
        # Check if move is legal (EXACT same logic as AI games)
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        if (row, col) not in legal_moves:
            return jsonify({'error': 'Illegal move'}), 400
        
        # Apply move (EXACT same logic as AI games)
        game['board'][row, col] = player
        update_small_board_status(game['board'], game['small_status'])
        
        # Check for winner (EXACT same logic as AI games)
        winner = check_big_board_winner(game['small_status'])
        if winner != 0:  # Someone actually won
            game['winner'] = winner
            game['game_over'] = True
        elif len(get_available_moves(game['board'], game['small_status'], game['current_board'])) == 0:
            # No winner but no moves left = draw
            game['winner'] = 0
            game['game_over'] = True
        
        # Only update stats when game actually ends
        if game['game_over']:
            import json
            board_json = json.dumps(game['board'].tolist())
            small_board_json = json.dumps(game['small_status'].tolist())
            
            # Determine if account owner won, lost, or drew
            account_owner_is_player1 = game.get('account_owner_is_player1', True)
            account_owner_result = game['winner']
            
            # Convert game winner to account owner's perspective
            if account_owner_is_player1:
                # Account owner is Player 1 (X = 1)
                account_owner_result = game['winner']  # 1 = won, -1 = lost, 0 = draw
            else:
                # Account owner is Player 2 (O = -1)
                if game['winner'] == 1:
                    account_owner_result = -1  # Player 1 won, so account owner lost
                elif game['winner'] == -1:
                    account_owner_result = 1   # Player 2 won, so account owner won
                else:
                    account_owner_result = 0   # Draw stays draw
            
            update_game_stats('pvp_local', None, account_owner_result, 1, board_json, small_board_json)
        
        # Determine next board (EXACT same logic as AI games)
        if not game['game_over']:
            ib, jb = row % SMALL_SIZE, col % SMALL_SIZE
            if game['small_status'][ib, jb] == 0:
                game['current_board'] = (ib, jb)
            else:
                game['current_board'] = None
            
            # Switch player for PvP
            game['current_player'] = -player
        
        legal_moves = get_available_moves(game['board'], game['small_status'], game['current_board'])
        
        return jsonify({
            'board': game['board'].tolist(),
            'small_status': game['small_status'].tolist(),
            'current_board': game['current_board'],
            'legal_moves': legal_moves,
            'winner': game['winner'],
            'game_over': game['game_over'],
            'current_player': game.get('current_player', PLAYER_X)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@game_bp.route('/api/pvp_reset/<int:game_id>', methods=['POST'])
def reset_pvp_game(game_id):
    """Reset a PvP game."""
    try:
        session_id = f"pvp_game_{game_id}"
        
        # Initialize new game with randomization
        board = create_board()
        small_status = create_small_board_status()
        current_board = None
        legal_moves = get_available_moves(board, small_status, current_board)
        
        # Randomly decide if account owner is Player 1 or Player 2
        import random
        account_owner_is_player1 = random.choice([True, False])
        starting_player = PLAYER_X if random.choice([True, False]) else PLAYER_O
        
        game_sessions[session_id] = {
            'board': board,
            'small_status': small_status,
            'current_board': current_board,
            'legal_moves': legal_moves,
            'winner': None,
            'game_over': False,
            'current_player': starting_player,
            'account_owner_is_player1': account_owner_is_player1
        }
        
        return jsonify({
            'board': board.tolist(),
            'small_status': small_status.tolist(),
            'current_board': current_board,
            'legal_moves': legal_moves,
            'winner': None,
            'game_over': False,
            'current_player': starting_player,
            'account_owner_is_player1': account_owner_is_player1
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
