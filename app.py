from flask import Flask, render_template, request, jsonify
from game.engine import (
    create_board,
    create_small_board_status,
    get_available_moves,
    update_small_board_status,
    check_big_board_winner,
    hard_ai_move,
    PLAYER_X,
    PLAYER_O,
    SMALL_SIZE
)

app = Flask(__name__)

game_state = {}

def init_game():
    """
    Initialize or reset the game state:
    - Empty board
    - All small boards status = 0 (ongoing)
    - Player turn = X
    - No restriction on next small board
    """
    game_state['board'] = create_board()
    game_state['small_status'] = create_small_board_status()
    game_state['player'] = PLAYER_X
    game_state['current_board'] = None

# Initialize on startup
init_game()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    """Reset to a brand-new game."""
    init_game()
    board = game_state['board']
    small_status = game_state['small_status']
    current_board = game_state['current_board']
    # Compute all legal moves for the fresh state
    legal_moves = get_available_moves(board, small_status, current_board)
    return jsonify({
        'board': board.tolist(),
        'small_status': small_status.tolist(),
        'current_board': current_board,
        'legal_moves': legal_moves,
        'winner': None
    })

@app.route('/move', methods=['POST'])
def player_move():
    data = request.get_json()
    row = data.get('row')
    col = data.get('col')

    board = game_state['board']
    small_status = game_state['small_status']
    current_board = game_state['current_board']
    player = game_state['player']

    # Turn order check
    if player != PLAYER_X:
        return jsonify({'error': 'Not player turn'}), 400

    # Legality check
    legal_moves = get_available_moves(board, small_status, current_board)
    if (row, col) not in legal_moves:
        return jsonify({'error': 'Illegal move'}), 400

    # Apply move
    board[row, col] = player
    update_small_board_status(board, small_status)

    # Check for winner in big board
    winner = check_big_board_winner(small_status)

    # Determine next small board
    ib, jb = row % SMALL_SIZE, col % SMALL_SIZE
    if small_status[ib, jb] == 0:
        game_state['current_board'] = (ib, jb)
    else:
        game_state['current_board'] = None

    # Switch to AI turn
    game_state['player'] = PLAYER_O

    # Compute new legal moves for AI
    legal_moves = get_available_moves(board, small_status, game_state['current_board'])

    return jsonify({
        'board': board.tolist(),
        'small_status': small_status.tolist(),
        'current_board': game_state['current_board'],
        'legal_moves': legal_moves,
        'winner': winner
    })

@app.route('/ai', methods=['POST'])
def ai_move():
    board = game_state['board']
    small_status = game_state['small_status']
    current_board = game_state['current_board']
    player = game_state['player']

    # Turn order check
    if player != PLAYER_O:
        return jsonify({'error': 'Not AI turn'}), 400

    # Compute best move
    move = hard_ai_move(board, small_status, current_board, player)
    if not move:
        return jsonify({'error': 'No moves available'}), 400
    row, col = move

    # Apply move
    board[row, col] = player
    update_small_board_status(board, small_status)

    # Check for winner
    winner = check_big_board_winner(small_status)

    # Determine next small board
    ib, jb = row % SMALL_SIZE, col % SMALL_SIZE
    if small_status[ib, jb] == 0:
        game_state['current_board'] = (ib, jb)
    else:
        game_state['current_board'] = None

    # Switch back to player turn
    game_state['player'] = PLAYER_X

    # Compute new legal moves for player
    legal_moves = get_available_moves(board, small_status, game_state['current_board'])

    return jsonify({
        'move': {'row': row, 'col': col},
        'board': board.tolist(),
        'small_status': small_status.tolist(),
        'current_board': game_state['current_board'],
        'legal_moves': legal_moves,
        'winner': winner
    })

if __name__ == '__main__':
    app.run(debug=True)
