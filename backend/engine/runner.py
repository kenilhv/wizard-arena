"""Run a single Connect-4 match between two harness instances, record replay
frames, meter LLM usage. A harness that errors, returns an illegal column, or
exceeds the per-move time limit forfeits the game."""
from __future__ import annotations
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, Dict, List

from .connect4 import Connect4, GameView
from .llm import LLM

MOVE_TIMEOUT = float(os.getenv("MOVE_TIMEOUT", "15"))
MAX_PLIES = 42


def _safe_move(harness, view: GameView, llm: LLM, pool: ThreadPoolExecutor):
    try:
        fut = pool.submit(harness.move, view, llm)
        col = fut.result(timeout=MOVE_TIMEOUT)
    except FutureTimeout:
        return None, "forfeit_timeout"
    except Exception as e:  # noqa: BLE001 - any harness crash is a forfeit
        return None, f"forfeit_error:{type(e).__name__}"
    if col not in view.legal_moves:
        return None, "forfeit_illegal"
    return int(col), None


def play_match(harness_a, name_a: str, harness_b, name_b: str) -> Dict[str, Any]:
    """Play one game. A is token 1 (moves first), B is token 2. Each side gets a
    fresh metered LLM using its own model (no-code harnesses set `.model`)."""
    game = Connect4()
    players = {
        1: ("A", name_a, harness_a, LLM(model=getattr(harness_a, "model", None))),
        2: ("B", name_b, harness_b, LLM(model=getattr(harness_b, "model", None))),
    }

    frames: List[Dict[str, Any]] = [{"board": game.snapshot(), "move": None, "mover": None, "ply": 0}]
    result: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "names": {"A": name_a, "B": name_b},
        "winner": None, "reason": None, "moves": [],
    }

    with ThreadPoolExecutor(max_workers=1) as pool:
        for ply in range(1, MAX_PLIES + 1):
            token = game.turn
            tag, _name, harness, llm = players[token]
            view = GameView(game, me=token)
            col, err = _safe_move(harness, view, llm, pool)
            if err is not None:
                result["winner"] = "B" if tag == "A" else "A"
                result["reason"] = err
                break
            game.play(col)
            result["moves"].append(col)
            frames.append({"board": game.snapshot(), "move": col, "mover": tag, "ply": ply})
            if game.is_over():
                if game.winner == 0:
                    result["winner"], result["reason"] = "draw", "draw"
                else:
                    result["winner"], result["reason"] = players[game.winner][0], "four_in_a_row"
                break

    if result["winner"] is None:
        result["winner"], result["reason"] = "draw", "max_plies"

    result["frames"] = frames
    result["usage"] = {"A": players[1][3].usage.as_dict(), "B": players[2][3].usage.as_dict()}
    return result
