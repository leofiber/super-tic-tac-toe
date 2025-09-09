import numpy as np
import random
import time

# ===== Constants =====
PLAYER_X = 1
PLAYER_O = -1
EMPTY = 0
BOARD_SIZE = 3
SMALL_SIZE = 3

# Small-board status encoding (consistent across engine & AIs)
SMALL_X = 1    # X won this small board
SMALL_O = 2    # O won this small board
SMALL_DRAW = 3 # small board is full / draw

MAX_DEPTH   = 7          # endgame minimax depth
MCTS_TIME   = 8.0        # seconds per Medium MCTS move (tune 5.0–8.0)
MAX_PLAYOUTS = 20000     # cap on MCTS simulations (guard with time too)

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
    if (br, bc) == (1, 1): weight += 3
    if (r % SMALL_SIZE, c % SMALL_SIZE) == (1, 1): weight += 2
    if (r % SMALL_SIZE, c % SMALL_SIZE) in [(0,0), (0,2), (2,0), (2,2)]: weight += 1
    return weight

# ---------- Evaluation ----------
def eval_line(line, player):
    """Score a 3-cell line relative to 'player'."""
    pm = np.sum(line == player)
    om = np.sum(line == -player)
    if om == 0 and pm > 0:
        return 10 ** pm
    if pm == 0 and om > 0:
        return - (10 ** om)
    return 0

def _small_owner(s):
    if s == SMALL_X: return PLAYER_X
    if s == SMALL_O: return PLAYER_O
    return 0

def evaluate_board(board, small_status, player):
    """Heuristic evaluation combining small boards, relative to 'player'."""
    score = 0
    cen_owner = _small_owner(small_status[1,1])
    if cen_owner == player: score += 500
    elif cen_owner == -player: score -= 500

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            s = small_status[i, j]
            if s in (SMALL_X, SMALL_O):
                score += 1000 if _small_owner(s) == player else -1000
            elif s == 0:
                sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                            j*SMALL_SIZE:(j+1)*SMALL_SIZE]
                for k in range(SMALL_SIZE):
                    score += eval_line(sub[k, :], player)
                    score += eval_line(sub[:, k], player)
                score += eval_line(np.diag(sub), player)
                score += eval_line(np.diag(np.fliplr(sub)), player)
    return score

# ---------- Winner Checks ----------
def check_small_board_winner(board, i, j):
    """Return +1 (X), -1 (O), or 0 for a 3×3 sub-board winner."""
    sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                j*SMALL_SIZE:(j+1)*SMALL_SIZE]
    for k in range(SMALL_SIZE):
        rs = int(sub[k, :].sum())
        if abs(rs) == SMALL_SIZE: return int(np.sign(rs))
        cs = int(sub[:, k].sum())
        if abs(cs) == SMALL_SIZE: return int(np.sign(cs))
    d1 = int(sum(sub[d, d] for d in range(SMALL_SIZE)))
    if abs(d1) == SMALL_SIZE: return int(np.sign(d1))
    d2 = int(sum(sub[d, SMALL_SIZE-1-d] for d in range(SMALL_SIZE)))
    if abs(d2) == SMALL_SIZE: return int(np.sign(d2))
    return 0

def update_small_board_status(board, small_status):
    """Update small_status in-place based on board state."""
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if small_status[i, j] != 0:
                continue
            w = check_small_board_winner(board, i, j)
            if w == PLAYER_X:
                small_status[i, j] = SMALL_X
            elif w == PLAYER_O:
                small_status[i, j] = SMALL_O
            else:
                sub = board[i*SMALL_SIZE:(i+1)*SMALL_SIZE,
                            j*SMALL_SIZE:(j+1)*SMALL_SIZE]
                if not (sub == EMPTY).any():
                    small_status[i, j] = SMALL_DRAW

def check_big_board_winner(small_status):
    """Return +1 (X), -1 (O), or 0 for the big board based on small_status."""
    for i in range(BOARD_SIZE):
        if all(small_status[i, j] == SMALL_X for j in range(BOARD_SIZE)): return PLAYER_X
        if all(small_status[i, j] == SMALL_O for j in range(BOARD_SIZE)): return PLAYER_O
        if all(small_status[j, i] == SMALL_X for j in range(BOARD_SIZE)): return PLAYER_X
        if all(small_status[j, i] == SMALL_O for j in range(BOARD_SIZE)): return PLAYER_O
    if all(small_status[d, d] == SMALL_X for d in range(BOARD_SIZE)): return PLAYER_X
    if all(small_status[d, d] == SMALL_O for d in range(BOARD_SIZE)): return PLAYER_O
    if all(small_status[d, BOARD_SIZE-1-d] == SMALL_X for d in range(BOARD_SIZE)): return PLAYER_X
    if all(small_status[d, BOARD_SIZE-1-d] == SMALL_O for d in range(BOARD_SIZE)): return PLAYER_O
    return 0

# ---------- Minimax (Endgame) ----------
transposition_table = {}

def state_key(board, small_status, current_board):
    return (tuple(board.flatten()), tuple(small_status.flatten()), current_board)

def minimax(board, small_status, current_board, player, depth, alpha, beta, start):
    winner = check_big_board_winner(small_status)
    if winner == PLAYER_X: return 10000 + depth
    if winner == PLAYER_O: return -10000 - depth
    if all(s != 0 for row in small_status for s in row): return 0
    if depth == 0 or time.time() - start > 1.0:
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
            best = max(best, val); alpha = max(alpha, val)
        else:
            best = min(best, val); beta = min(beta, val)
        if beta <= alpha: break
    transposition_table[key] = (depth, best)
    return best

# ---------- Safe small-capture helpers (minimal tactical layer) ----------

def _macro_two_in_row_potential(small_status, owner):
    lines = []
    for i in range(BOARD_SIZE):
        lines.append([small_status[i,0], small_status[i,1], small_status[i,2]])
        lines.append([small_status[0,i], small_status[1,i], small_status[2,i]])
    lines.append([small_status[0,0], small_status[1,1], small_status[2,2]])
    lines.append([small_status[0,2], small_status[1,1], small_status[2,0]])
    target = SMALL_X if owner == PLAYER_X else SMALL_O
    cnt = 0
    for L in lines:
        owns = sum(1 for x in L if x == target)
        opens = sum(1 for x in L if x == 0)
        if owns == 2 and opens == 1:
            cnt += 1
    return cnt


def _makes_small_capture(board, move, player):
    r, c = move
    bi, bj = r // SMALL_SIZE, c // SMALL_SIZE
    tb = board.copy(); tb[r, c] = player
    return check_small_board_winner(tb, bi, bj) == player


def _small_capture_candidates(board, small_status, current_board, player):
    return [m for m in get_available_moves(board, small_status, current_board)
            if _makes_small_capture(board, m, player)]


def _is_capture_safe(board, small_status, current_board, move, player):
    # Simulate our capture
    r, c = move
    tb, ts = board.copy(), small_status.copy()
    tb[r, c] = player
    update_small_board_status(tb, ts)

    # Where do we send opponent next?
    nb = (r % SMALL_SIZE, c % SMALL_SIZE) if ts[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
    opp = -player

    # If opponent has any reply that INSTANTLY wins the big board, it's unsafe.
    if nb is not None:
        for (rr, cc) in get_available_moves(tb, ts, nb):
            t2b, t2s = tb.copy(), ts.copy()
            t2b[rr, cc] = opp
            update_small_board_status(t2b, t2s)
            if check_big_board_winner(t2s) == opp:
                return False
    else:
        # anywhere-next: check all legal replies
        for (rr, cc) in get_available_moves(tb, ts, None):
            t2b, t2s = tb.copy(), ts.copy()
            t2b[rr, cc] = opp
            update_small_board_status(t2b, t2s)
            if check_big_board_winner(t2s) == opp:
                return False

    # Avoid giving opponent an immediate small capture in a high-value macro board,
    # or a reply that creates at least one macro 2-in-a-row for them.
    replies = get_available_moves(tb, ts, nb)
    for (rr, cc) in replies:
        bi, bj = rr // SMALL_SIZE, cc // SMALL_SIZE
        # immediate small capture?
        t2b = tb.copy(); t2b[rr, cc] = opp
        if check_small_board_winner(t2b, bi, bj) == opp:
            # weight macro importance: center > corners > edges
            if (bi, bj) == (1, 1):
                return False
            if (bi, bj) in [(0,0), (0,2), (2,0), (2,2)]:
                return False
        # check macro two-in-row potential after opponent reply
        t2s = ts.copy(); update_small_board_status(t2b, t2s)
        if _macro_two_in_row_potential(t2s, opp) >= 1:
            return False

    return True

# ---------- Proper PUCT-based MCTS (Medium AI, classic feel) ----------
class _Node:
    __slots__ = ("parent","children","N","W","Q","P","move","player")
    def __init__(self, parent, move, player, prior):
        self.parent = parent
        self.children = {}
        self.N = 0
        self.W = 0.0
        self.Q = 0.0
        self.P = prior
        self.move = move
        self.player = player  # player who will play at this node


def _legal_with_priors(board, small_status, current_board):
    moves = get_available_moves(board, small_status, current_board)
    if not moves:
        return [], {}
    hs = [max(1, score_move(m)) for m in moves]
    tot = float(sum(hs))
    pri = {m: (h/tot) for m,h in zip(moves, hs)}
    return moves, pri


def _puct_select(node, c_puct=1.6):
    sN = (node.N + 1) ** 0.5
    best, best_child, best_move = -1e18, None, None
    for m, ch in node.children.items():
        u = ch.Q + c_puct * ch.P * sN / (1 + ch.N)
        if u > best:
            best, best_child, best_move = u, ch, m
    return best_move, best_child


def _tanh_value(score, scale=1200.0):
    # squash heuristic evaluation into [-1, 1]
    import math
    return math.tanh(score / scale)


def _mcts_search(board, small_status, current_board, player, time_limit, max_playouts):
    t0 = time.time()
    root = _Node(None, None, player, 1.0)
    moves, pri = _legal_with_priors(board, small_status, current_board)
    for m in moves:
        root.children[m] = _Node(root, m, -player, pri[m])

    iters = 0
    while iters < max_playouts and (time.time() - t0) < time_limit:
        iters += 1
        node = root
        # copy state
        b = board.copy(); s = small_status.copy(); cb = current_board; p = player
        path = [node]

        # SELECTION
        while node.children:
            m, node = _puct_select(node)
            r, c = m
            b[r, c] = p
            update_small_board_status(b, s)
            cb = (r % SMALL_SIZE, c % SMALL_SIZE) if s[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
            p = -p
            path.append(node)
            w = check_big_board_winner(s)
            if w != 0 or not get_available_moves(b, s, cb):
                v = 1 if w == path[0].player else -1 if w == -path[0].player else 0
                # BACKPROP
                for nd in reversed(path):
                    nd.N += 1
                    nd.W += v
                    nd.Q = nd.W / nd.N
                    v = -v
                break
        else:
            # EXPANSION
            w = check_big_board_winner(s)
            if w != 0:
                v = 1 if w == path[0].player else -1 if w == -path[0].player else 0
            else:
                avail, pri2 = _legal_with_priors(b, s, cb)
                if not avail:
                    v = 0
                else:
                    # bootstrap with heuristic evaluation at expansion
                    for m2 in avail:
                        node.children[m2] = _Node(node, m2, p, pri2[m2])
                    v = _tanh_value(evaluate_board(b, s, path[0].player))
            # BACKPROP
            for nd in reversed(path):
                nd.N += 1
                nd.W += v
                nd.Q = nd.W / nd.N
                v = -v

    # choose action with max visits
    if not root.children:
        # no legal moves (shouldn't happen unless terminal)
        return None
    best = max(root.children.items(), key=lambda kv: kv[1].N)[0]
    return best


def mcts_ai_move(board, small_status, current_board, player):
    """Medium AI: classic PUCT with simple priors + leaf bootstrap, plus safe captures."""
    # Early opening: keep your book behavior
    empties = int(np.sum(board == EMPTY))
    total = BOARD_SIZE * SMALL_SIZE * BOARD_SIZE * SMALL_SIZE
    if empties == total:
        return opening_book[0]
    if empties == total - 1:
        avail = set(get_available_moves(board, small_status, current_board))
        for mv in opening_book[1:]:
            if mv in avail:
                return mv

    # Take safe small-board wins if available (minimal tactical layer)
    caps = _small_capture_candidates(board, small_status, current_board, player)
    if caps:
        safe_caps = [m for m in caps if _is_capture_safe(board, small_status, current_board, m, player)]
        if safe_caps:
            def _macro_w(mv):
                bi, bj = mv[0]//SMALL_SIZE, mv[1]//SMALL_SIZE
                if (bi, bj) == (1, 1): return 3.0
                if (bi, bj) in [(0,0), (0,2), (2,0), (2,2)]: return 2.0
                return 1.0
            safe_caps.sort(key=_macro_w, reverse=True)
            return safe_caps[0]

    best = _mcts_search(board, small_status, current_board, player,
                        time_limit=MCTS_TIME, max_playouts=MAX_PLAYOUTS)
    if best is None:
        moves = get_available_moves(board, small_status, current_board)
        return random.choice(moves) if moves else None
    return best

# ---------- Legacy Hybrid Hard AI (kept for compatibility) ----------
def hard_ai_move(board, small_status, current_board, player):
    """Legacy hard AI kept for compatibility; routes to MCTS midgame + minimax endgame."""
    empties = int(np.sum(board == EMPTY))
    total = BOARD_SIZE * SMALL_SIZE * BOARD_SIZE * SMALL_SIZE
    if empties == total:
        return opening_book[0]
    if empties == total - 1:
        avail = set(get_available_moves(board, small_status, current_board))
        for mv in opening_book[1:]:
            if mv in avail:
                return mv
    # midgame: use classic MCTS
    if empties > 20:
        return mcts_ai_move(board, small_status, current_board, player)
    # endgame: minimax
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
    return best_move or (random.choice(get_available_moves(board, small_status, current_board))
                         if get_available_moves(board, small_status, current_board) else None)
