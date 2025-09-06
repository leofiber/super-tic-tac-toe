import numpy as np
import random
import time

# Constants
PLAYER_X = 1
PLAYER_O = -1
EMPTY = 0
BOARD_SIZE = 3
SMALL_SIZE = 3
MAX_DEPTH = 7        # depth limit for minimax endgame
MCTS_TIME = 8.0      # seconds per MCTS move
MAX_PLAYOUTS = 2000  # cap on playouts per move

# Opening book moves (center, then corners)
opening_book = [(4, 4), (0, 0), (0, 8), (8, 0), (8, 8)]

# ---------- Board Initialization ----------
def create_board():
    """Return an empty 9×9 board."""
    return np.zeros((BOARD_SIZE * SMALL_SIZE, BOARD_SIZE * SMALL_SIZE), dtype=int)


def create_small_board_status():
    """Return a 3×3 status board: 0=ongoing,1=X won,2=O won,3=draw."""
    return np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

# ---------- Move Generation ----------
def get_available_moves(board, small_status, current_board):
    """List legal (r, c) moves."""
    moves = []
    if current_board is not None:
        bi, bj = current_board
        if small_status[bi, bj] == 0:
            for r in range(bi*SMALL_SIZE, (bi+1)*SMALL_SIZE):
                for c in range(bj*SMALL_SIZE, (bj+1)*SMALL_SIZE):
                    if board[r, c] == EMPTY:
                        moves.append((r, c))
            if moves:
                return moves
    # fallback: any empty cell in unfinished small boards
    for r in range(BOARD_SIZE * SMALL_SIZE):
        for c in range(BOARD_SIZE * SMALL_SIZE):
            if board[r, c] == EMPTY and small_status[r//SMALL_SIZE, c//SMALL_SIZE] == 0:
                moves.append((r, c))
    return moves

# ---------- Move Ordering (Heuristic) ----------
def score_move(move):
    """Simple heuristic: prioritize center board, center cell, then corners."""
    r, c = move
    weight = 0
    br, bc = r // SMALL_SIZE, c // SMALL_SIZE
    # prioritize center small board
    if (br, bc) == (1, 1):
        weight += 3
    # prioritize center cell of sub-board
    if (r % SMALL_SIZE, c % SMALL_SIZE) == (1, 1):
        weight += 2
    # corners of sub-board
    if (r % SMALL_SIZE, c % SMALL_SIZE) in [(0,0), (0,2), (2,0), (2,2)]:
        weight += 1
    return weight

# ---------- Evaluation ----------
def eval_line(line, player):
    """Score a 3-cell line."""
    pm = np.sum(line == player)
    om = np.sum(line == -player)
    if om == 0 and pm > 0:
        return 10 ** pm
    if pm == 0 and om > 0:
        return - (10 ** om)
    return 0


def evaluate_board(board, small_status, player):
    """Heuristic evaluation combining small boards."""
    score = 0
    # big-board center weight
    if small_status[1,1] == player:
        score += 500
    elif small_status[1,1] == -player:
        score -= 500
    # small-board contributions
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            s = small_status[i, j]
            if s == 1:
                score += 1000
            elif s == 2:
                score -= 1000
            elif s == 0:
                sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                            j*SMALL_SIZE:(j+1)*SMALL_SIZE]
                # rows and cols
                for k in range(SMALL_SIZE):
                    score += eval_line(sub[k, :], player)
                    score += eval_line(sub[:, k], player)
                # diagonals
                score += eval_line(np.diag(sub), player)
                score += eval_line(np.diag(np.fliplr(sub)), player)
    return score

# ---------- Winner Checks ----------
def check_small_board_winner(board, i, j):
    """Return +1, -1, or 0 for a 3×3 sub-board."""
    sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                j*SMALL_SIZE:(j+1)*SMALL_SIZE]
    # rows and cols
    for k in range(SMALL_SIZE):
        rs = sub[k, :].sum()
        if abs(rs) == SMALL_SIZE:
            return np.sign(rs)
        cs = sub[:, k].sum()
        if abs(cs) == SMALL_SIZE:
            return np.sign(cs)
    # diagonals
    d1 = sum(sub[d, d] for d in range(SMALL_SIZE))
    if abs(d1) == SMALL_SIZE:
        return np.sign(d1)
    d2 = sum(sub[d, SMALL_SIZE-1-d] for d in range(SMALL_SIZE))
    if abs(d2) == SMALL_SIZE:
        return np.sign(d2)
    return 0


def update_small_board_status(board, small_status):
    """Update small_status in-place based on board."""
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if small_status[i, j] != 0:
                continue
            w = check_small_board_winner(board, i, j)
            if w == PLAYER_X:
                small_status[i, j] = 1
            elif w == PLAYER_O:
                small_status[i, j] = -1
            else:
                sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                            j*SMALL_SIZE:(j+1)*SMALL_SIZE]
                if not (sub == EMPTY).any():
                    small_status[i, j] = 3


def check_big_board_winner(small_status):
    """Return +1, -1, or 0 for the big board based on small_status."""
    for i in range(BOARD_SIZE):
        if all(small_status[i, j] == 1 for j in range(BOARD_SIZE)):
            return PLAYER_X
        if all(small_status[i, j] == -1 for j in range(BOARD_SIZE)):
            return PLAYER_O
        if all(small_status[j, i] == 1 for j in range(BOARD_SIZE)):
            return PLAYER_X
        if all(small_status[j, i] == -1 for j in range(BOARD_SIZE)):
            return PLAYER_O
    # diagonals
    if all(small_status[d, d] == 1 for d in range(BOARD_SIZE)):
        return PLAYER_X
    if all(small_status[d, d] == -1 for d in range(BOARD_SIZE)):
        return PLAYER_O
    if all(small_status[d, BOARD_SIZE-1-d] == 1 for d in range(BOARD_SIZE)):
        return PLAYER_X
    if all(small_status[d, BOARD_SIZE-1-d] == -1 for d in range(BOARD_SIZE)):
        return PLAYER_O
    return 0

# ---------- Minimax (Endgame) ----------
transposition_table = {}

def state_key(board, small_status, current_board):
    return (tuple(board.flatten()), tuple(small_status.flatten()), current_board)


def minimax(board, small_status, current_board, player, depth, alpha, beta, start):
    winner = check_big_board_winner(small_status)
    if winner == PLAYER_X:
        return 10000 + depth
    if winner == PLAYER_O:
        return -10000 - depth
    if all(s != 0 for row in small_status for s in row):
        return 0
    if depth == 0 or time.time() - start > 1:
        return evaluate_board(board, small_status, player)

    key = state_key(board, small_status, current_board)
    if key in transposition_table and transposition_table[key][0] >= depth:
        return transposition_table[key][1]

    moves = get_available_moves(board, small_status, current_board)
    moves.sort(key=lambda mv: score_move(mv), reverse=True)
    best = -float('inf') if player == PLAYER_X else float('inf')
    for r, c in moves:
        b2, s2 = board.copy(), small_status.copy()
        b2[r, c] = player
        update_small_board_status(b2, s2)
        nb = (r % SMALL_SIZE, c % SMALL_SIZE) if s2[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
        val = minimax(b2, s2, nb, -player, depth-1, alpha, beta, start)
        if player == PLAYER_X:
            best = max(best, val)
            alpha = max(alpha, val)
        else:
            best = min(best, val)
            beta = min(beta, val)
        if beta <= alpha:
            break
    transposition_table[key] = (depth, best)
    return best

# ---------- MCTS Wrapper ----------
def mcts_ai_move(board, small_status, current_board, player):
    moves = get_available_moves(board, small_status, current_board)
    wins = {mv: 0 for mv in moves}
    start = time.time()
    sims = 0
    while sims < MAX_PLAYOUTS and (time.time() - start) < MCTS_TIME:
        sims += 1
        for mv in moves:
            r, c = mv
            b2, s2 = board.copy(), small_status.copy()
            b2[r, c] = player
            update_small_board_status(b2, s2)
            nb = (r % SMALL_SIZE, c % SMALL_SIZE) if s2[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
            # simulate random playout
            pl = -player
            cb = nb
            winner = None
            board_cp, status_cp = b2.copy(), s2.copy()
            while True:
                w = check_big_board_winner(status_cp)
                if w != 0:
                    winner = w
                    break
                avail = get_available_moves(board_cp, status_cp, cb)
                if not avail:
                    winner = 0
                    break
                rr, cc = random.choice(avail)
                board_cp[rr, cc] = pl
                update_small_board_status(board_cp, status_cp)
                cb = (rr % SMALL_SIZE, cc % SMALL_SIZE) if status_cp[rr//SMALL_SIZE, cc//SMALL_SIZE] == 0 else None
                pl = -pl
            if winner == player:
                wins[mv] += 1
    # choose move with max win count
    return max(wins.items(), key=lambda kv: kv[1])[0]

# ---------- Hybrid Hard AI ----------
def hard_ai_move(board, small_status, current_board, player):
    empties = np.sum(board == EMPTY)
    total = BOARD_SIZE * SMALL_SIZE * BOARD_SIZE * SMALL_SIZE
    # opening book
    if empties == total:
        return opening_book[0]
    if empties == total - 1:
        for mv in opening_book[1:]:
            if mv in get_available_moves(board, small_status, current_board):
                return mv
    # midgame MCTS
    if empties > 20:
        return mcts_ai_move(board, small_status, current_board, player)
    # endgame minimax
    start = time.time()
    transposition_table.clear()
    best_score = -float('inf')
    best_move = None
    for mv in get_available_moves(board, small_status, current_board):
        r, c = mv
        b2, s2 = board.copy(), small_status.copy()
        b2[r, c] = player
        update_small_board_status(b2, s2)
        nb = (r % SMALL_SIZE, c % SMALL_SIZE) if s2[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
        score = minimax(b2, s2, nb, -player, MAX_DEPTH, -float('inf'), float('inf'), start)
        if score > best_score:
            best_score, best_move = score, mv
    return best_move or random.choice(get_available_moves(board, small_status, current_board))
