#!/usr/bin/env python3
"""
tournament.py — Head-to-head Medium (engine.mcts_ai_move) vs Hard (advanced_ai.AdvancedAI)
Run:  python tournament.py --games 50
Optional knobs:
  --medium-time 5.0            # seconds per Medium move
  --medium-playouts 15000      # playout cap
  --hard-midgame-time 7.0      # seconds per Hard midgame move (if supported)
  --hard-playouts 40000        # playout cap for Hard (if supported)
  --seed 123                   # set RNG seed
"""

import argparse
import importlib
import sys
import time

def import_modules():
    # Prefer package-style imports (game.engine / game.advanced_ai) to match your app layout.
    tried = []
    for eng_mod, adv_mod in [
        ("game.engine", "game.advanced_ai"),
        ("engine", "advanced_ai"),
    ]:
        try:
            engine = importlib.import_module(eng_mod)
            adv    = importlib.import_module(adv_mod)
            return engine, adv, (eng_mod, adv_mod)
        except Exception as e:
            tried.append((eng_mod, adv_mod, repr(e)))
    lines = ["Failed to import engine/advanced_ai. Tried:"]
    for eng_mod, adv_mod, err in tried:
        lines.append(f"  {eng_mod} / {adv_mod}: {err}")
    raise RuntimeError("\n".join(lines))

def set_budgets(engine, adv, args):
    # Medium budgets (engine)
    if args.medium_time is not None and hasattr(engine, "MCTS_TIME"):
        engine.MCTS_TIME = float(args.medium_time)
    if args.medium_playouts is not None and hasattr(engine, "MAX_PLAYOUTS"):
        engine.MAX_PLAYOUTS = int(args.medium_playouts)

    # Hard budgets (advanced AI instance exposed as advanced_ai)
    if hasattr(adv, "advanced_ai"):
        if args.hard_midgame_time is not None and hasattr(adv.advanced_ai, "MIDGAME_TIME"):
            adv.advanced_ai.MIDGAME_TIME = float(args.hard_midgame_time)
        if args.hard_playouts is not None and hasattr(adv.advanced_ai, "PLAYOUTS"):
            adv.advanced_ai.PLAYOUTS = int(args.hard_playouts)

def legal_or_random(engine, board, small_status, current_board, player, move_func):
    moves = engine.get_available_moves(board, small_status, current_board)
    if not moves:
        return None
    try:
        mv = move_func(board.copy(), small_status.copy(), current_board, player)
        if mv in moves:
            return mv
    except Exception:
        pass
    # fallback: pick any legal
    import random
    return random.choice(moves)

def apply_move(engine, board, small_status, move):
    r, c = move
    board[r, c] = engine.PLAYER_X if board[r, c] == 0 and (board == 0).sum() % 2 == board.size % 2 else board[r, c]
    # We won't rely on that; caller sets the player on write. Keep engine's update only.
    engine.update_small_board_status(board, small_status)
    bi, bj = r // engine.SMALL_SIZE, c // engine.SMALL_SIZE
    if small_status[bi, bj] == 0:
        next_board = (r % engine.SMALL_SIZE, c % engine.SMALL_SIZE)
    else:
        next_board = None
    return next_board

def play_game(engine, adv, hard_as_x: bool, max_plies=2000, verbose=False):
    import numpy as np
    board = engine.create_board()
    small_status = engine.create_small_board_status()
    current_board = None
    player = engine.PLAYER_X  # X starts
    moves = 0

    while True:
        w = engine.check_big_board_winner(small_status)
        if w != 0:
            if (w == engine.PLAYER_X and hard_as_x) or (w == engine.PLAYER_O and not hard_as_x):
                return "hard", moves
            else:
                return "medium", moves

        avail = engine.get_available_moves(board, small_status, current_board)
        if not avail or moves >= max_plies:
            return "draw", moves

        if player == engine.PLAYER_X:
            if hard_as_x:
                mv = legal_or_random(engine, board, small_status, current_board, player, adv.advanced_ai.get_move)
            else:
                mv = legal_or_random(engine, board, small_status, current_board, player, engine.mcts_ai_move)
        else:
            if hard_as_x:
                mv = legal_or_random(engine, board, small_status, current_board, player, engine.mcts_ai_move)
            else:
                mv = legal_or_random(engine, board, small_status, current_board, player, adv.advanced_ai.get_move)

        if mv is None:
            return "draw", moves

        r, c = mv
        board[r, c] = player
        engine.update_small_board_status(board, small_status)
        bi, bj = r // engine.SMALL_SIZE, c // engine.SMALL_SIZE
        if small_status[bi, bj] == 0:
            current_board = (r % engine.SMALL_SIZE, c % engine.SMALL_SIZE)
        else:
            current_board = None

        player = -player
        moves += 1
        if verbose and moves % 40 == 0:
            print("...plies:", moves)

def run_tournament(n_games, engine, adv, verbose=False):
    results = {"hard": 0, "medium": 0, "draw": 0}
    plies_sum = 0
    for i in range(n_games):
        hard_as_x = (i % 2 == 0)
        winner, plies = play_game(engine, adv, hard_as_x, verbose=verbose)
        results[winner] += 1
        plies_sum += plies
        if verbose:
            print(f"Game {i+1}/{n_games}: winner={winner}, plies={plies}")
    return results, (plies_sum / max(1, n_games))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=50)
    p.add_argument("--medium-time", type=float, default=None)
    p.add_argument("--medium-playouts", type=int, default=None)
    p.add_argument("--hard-midgame-time", type=float, default=None)
    p.add_argument("--hard-playouts", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.seed is not None:
        import random, numpy as np
        random.seed(args.seed)
        np.random.seed(args.seed)

    engine, adv, modnames = import_modules()
    set_budgets(engine, adv, args)

    t0 = time.time()
    results, avg_plies = run_tournament(args.games, engine, adv, verbose=args.verbose)
    dt = time.time() - t0

    hard = results["hard"]
    medium = results["medium"]
    draw = results["draw"]
    total = hard + medium + draw
    hard_pct = (100.0 * hard) / max(1, total - draw)
    medium_pct = (100.0 * medium) / max(1, total - draw)

    print("\n=== Tournament Results (Hard vs Medium) ===")
    print(f"Imports: engine={modnames[0]}  advanced_ai={modnames[1]}")
    print(f"Games: {total}   Hard: {hard}   Medium: {medium}   Draws: {draw}")
    print(f"Non-draw winrate — Hard: {hard_pct:.1f}%   Medium: {medium_pct:.1f}%")
    print(f"Average plies/game: {avg_plies:.1f}   Elapsed: {dt:.2f}s")

if __name__ == "__main__":
    main()
