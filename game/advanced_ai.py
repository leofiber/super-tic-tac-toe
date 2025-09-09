
"""
Advanced AI implementation for Hard difficulty
Upgraded: strategic heuristics + PUCT midgame + endgame solver
"""
import numpy as np
import random
import time
from game.engine import (
    get_available_moves, check_small_board_winner, check_big_board_winner,
    update_small_board_status, evaluate_board,
    PLAYER_X, PLAYER_O, EMPTY, SMALL_SIZE, BOARD_SIZE,
    SMALL_X, SMALL_O, SMALL_DRAW
)

class AdvancedAI:
    def __init__(self):
        self.SMALL_BOARD_WIN = 10000
        self.BIG_BOARD_WIN = 1000000
        self.CENTER_BONUS = 500
        self.CORNER_BONUS = 200
        self.EDGE_BONUS = 100
        self.THREAT_PENALTY = -5000
        self.STRATEGIC_DEPTH = 10  # deep but safe under time cap
        self.MIDGAME_TIME = 7.0
        self.PLAYOUTS = 40000

        self.opening_book = [
            (4, 4),
            (4, 1), (4, 7), (1, 4), (7, 4),
            (0, 0), (0, 8), (8, 0), (8, 8),
            (2, 2), (2, 6), (6, 2), (6, 6),
        ]

    # ========= Public API =========
    def get_move(self, board, small_status, current_board, player):
        empties = int(np.sum(board == EMPTY))
        total = BOARD_SIZE * SMALL_SIZE * BOARD_SIZE * SMALL_SIZE

        if empties >= total - 5:
            m = self._opening_move(board, small_status, current_board)
            if m is not None:
                return m

        w = self._find_immediate_win(board, small_status, current_board, player)
        if w: return w
        b = self._find_critical_block(board, small_status, current_board, player)
        if b: return b

        if empties > 18:
            return self._puct_midgame(board, small_status, current_board, player)
        else:
            return self._deep_endgame(board, small_status, current_board, player)

    # ========= Opening =========
    def _opening_move(self, board, small_status, current_board):
        moves = get_available_moves(board, small_status, current_board)
        s = set(moves)
        for mv in self.opening_book:
            if mv in s:
                return mv
        for move in moves:
            r, c = move
            if (r % SMALL_SIZE, c % SMALL_SIZE) == (1, 1):
                return move
        return random.choice(moves) if moves else None

    # ========= Immediate tactics =========
    def _find_immediate_win(self, board, small_status, current_board, player):
        for r, c in get_available_moves(board, small_status, current_board):
            tb, ts = board.copy(), small_status.copy()
            tb[r, c] = player
            update_small_board_status(tb, ts)
            if check_big_board_winner(ts) == player:
                return (r, c)
        return None

    def _find_critical_block(self, board, small_status, current_board, player):
        opp = -player
        moves = get_available_moves(board, small_status, current_board)
        for r, c in moves:
            tb, ts = board.copy(), small_status.copy()
            tb[r, c] = opp
            update_small_board_status(tb, ts)
            if check_big_board_winner(ts) == opp:
                return (r, c)

        # micro-board imminent wins
        best = None; best_w = -1e18
        for r, c in moves:
            bi, bj = r // SMALL_SIZE, c // SMALL_SIZE
            tb = board.copy(); tb[r, c] = opp
            if check_small_board_winner(tb, bi, bj) == opp:
                w = self._small_board_weight(bi, bj, small_status)
                if w > best_w:
                    best_w, best = w, (r, c)
        return best

    # ========= Midgame: PUCT with strategic priors =========
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
            self.player = player

    def _legal_with_priors(self, board, small_status, current_board, player):
        moves = get_available_moves(board, small_status, current_board)
        if not moves: return [], {}
        hs = []
        for (r, c) in moves:
            bi, bj = r // SMALL_SIZE, c // SMALL_SIZE
            ci, cj = r % SMALL_SIZE, c % SMALL_SIZE
            w = 1.0
            if (bi, bj) == (1, 1): w += 2.5
            if (ci, cj) == (1, 1): w += 1.5
            if (ci, cj) in [(0,0),(0,2),(2,0),(2,2)]: w += 0.75
            # send-to control
            # simulate only target info cheaply
            target_open = (small_status[ci, cj] == 0)
            if target_open: w += 0.6
            # anywhere-next
            tb, ts = board, small_status
            if ts[r//SMALL_SIZE, c//SMALL_SIZE] != 0:  # playing on a finished small board (shouldn't happen), small bonus none
                pass
            # heuristic: if target small board already won or draw -> anywhere-next
            if small_status[ci, cj] in (SMALL_X, SMALL_O, SMALL_DRAW):
                w += 1.2
            hs.append(w)
        tot = float(sum(hs)) or 1.0
        pri = {m: (w/tot) for m, w in zip(moves, hs)}
        return moves, pri

    def _puct_select(self, node, c_puct=1.8):
        sN = (node.N + 1) ** 0.5
        best, best_child, best_move = -1e18, None, None
        for m, ch in node.children.items():
            u = ch.Q + c_puct * ch.P * sN / (1 + ch.N)
            if u > best:
                best, best_child, best_move = u, ch, m
        return best_move, best_child

    def _tanh_value(self, board, small_status, ref_player):
        import math
        return math.tanh(evaluate_board(board, small_status, ref_player) / 1400.0)

    def _puct_midgame(self, board, small_status, current_board, player):
        t0 = time.time()
        root = self._Node(None, None, player, 1.0)
        moves, pri = self._legal_with_priors(board, small_status, current_board, player)
        for m in moves:
            root.children[m] = self._Node(root, m, -player, pri[m])

        iters = 0
        while iters < self.PLAYOUTS and (time.time() - t0) < self.MIDGAME_TIME:
            iters += 1
            node = root
            b = board.copy(); s = small_status.copy(); cb = current_board; p = player
            path = [node]

            # selection
            while node.children:
                m, node = self._puct_select(node)
                r, c = m
                b[r, c] = p
                update_small_board_status(b, s)
                cb = (r % SMALL_SIZE, c % SMALL_SIZE) if s[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
                p = -p
                path.append(node)
                w = check_big_board_winner(s)
                if w != 0 or not get_available_moves(b, s, cb):
                    v = 1 if w == path[0].player else -1 if w == -path[0].player else 0
                    for nd in reversed(path):
                        nd.N += 1; nd.W += v; nd.Q = nd.W/nd.N; v = -v
                    break
            else:
                # expand & evaluate
                w = check_big_board_winner(s)
                if w != 0:
                    v = 1 if w == path[0].player else -1 if w == -path[0].player else 0
                else:
                    avail, pri2 = self._legal_with_priors(b, s, cb, p)
                    if not avail:
                        v = 0
                    else:
                        for m2 in avail:
                            node.children[m2] = self._Node(node, m2, p, pri2[m2])
                        v = self._tanh_value(b, s, path[0].player)
                for nd in reversed(path):
                    nd.N += 1; nd.W += v; nd.Q = nd.W/nd.N; v = -v

        if not root.children:
            ms = get_available_moves(board, small_status, current_board)
            return random.choice(ms) if ms else None
        return max(root.children.items(), key=lambda kv: kv[1].N)[0]

    # ========= Endgame =========
    def _deep_endgame(self, board, small_status, current_board, player):
        start_time = time.time()
        best_move = None
        best_score = -float('inf') if player == PLAYER_X else float('inf')
        moves = get_available_moves(board, small_status, current_board)
        moves.sort(key=lambda m: self._pos_value(m[0], m[1], board, small_status), reverse=(player==PLAYER_X))
        for move in moves:
            if time.time() - start_time > 5.0: break
            r, c = move
            tb, ts = board.copy(), small_status.copy()
            tb[r, c] = player
            update_small_board_status(tb, ts)
            nb = (r % SMALL_SIZE, c % SMALL_SIZE) if ts[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
            sc = self._ab(tb, ts, nb, -player, self.STRATEGIC_DEPTH, -float('inf'), float('inf'), start_time)
            if player == PLAYER_X and sc > best_score:
                best_score, best_move = sc, move
            elif player == PLAYER_O and sc < best_score:
                best_score, best_move = sc, move
        return best_move or random.choice(moves)

    def _ab(self, board, small_status, current_board, player, depth, alpha, beta, t0):
        if time.time() - t0 > 4.5:
            return evaluate_board(board, small_status, player)
        w = check_big_board_winner(small_status)
        if w == PLAYER_X: return self.BIG_BOARD_WIN + depth
        if w == PLAYER_O: return -self.BIG_BOARD_WIN - depth
        if all(s != 0 for row in small_status for s in row): return 0
        if depth == 0: return evaluate_board(board, small_status, player)

        moves = get_available_moves(board, small_status, current_board)
        if not moves: return 0
        moves.sort(key=lambda m: self._pos_value(m[0], m[1], board, small_status), reverse=(player==PLAYER_X))
        if player == PLAYER_X:
            v = -float('inf')
            for (r,c) in moves:
                tb, ts = board.copy(), small_status.copy()
                tb[r,c] = player; update_small_board_status(tb, ts)
                nb = (r % SMALL_SIZE, c % SMALL_SIZE) if ts[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
                v = max(v, self._ab(tb, ts, nb, -player, depth-1, alpha, beta, t0))
                alpha = max(alpha, v)
                if beta <= alpha: break
            return v
        else:
            v = float('inf')
            for (r,c) in moves:
                tb, ts = board.copy(), small_status.copy()
                tb[r,c] = player; update_small_board_status(tb, ts)
                nb = (r % SMALL_SIZE, c % SMALL_SIZE) if ts[r//SMALL_SIZE, c//SMALL_SIZE] == 0 else None
                v = min(v, self._ab(tb, ts, nb, -player, depth-1, alpha, beta, t0))
                beta = min(beta, v)
                if beta <= alpha: break
            return v

    # ========= Heuristics =========
    def _small_board_weight(self, i, j, small_status):
        base = 1.0
        if (i, j) == (1, 1): base *= 2.0
        elif (i, j) in [(0,0),(0,2),(2,0),(2,2)]: base *= 1.5
        return base

    def _pos_value(self, r, c, board, small_status):
        bi, bj = r // SMALL_SIZE, c // SMALL_SIZE
        ci, cj = r % SMALL_SIZE, c % SMALL_SIZE
        s = 0
        if (bi, bj) == (1,1): s += self.CENTER_BONUS
        elif (bi, bj) in [(0,0),(0,2),(2,0),(2,2)]: s += self.CORNER_BONUS
        else: s += self.EDGE_BONUS
        if (ci, cj) == (1,1): s += self.CENTER_BONUS//2
        elif (ci, cj) in [(0,0),(0,2),(2,0),(2,2)]: s += self.CORNER_BONUS//2
        # anywhere-next bonus
        target = (ci, cj)
        if small_status[target[0], target[1]] in (SMALL_X, SMALL_O, SMALL_DRAW):
            s += 250
        return s

# Global instance for use in ai_service
advanced_ai = AdvancedAI()
