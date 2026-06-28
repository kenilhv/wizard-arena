"""Connect-4: head-to-head problem. Reuses the engine + tournament; adds no-code
hooks so form-built harnesses can compete too."""
from __future__ import annotations
import os
import re

from engine.tournament import run_tournament
from harness import load_code_harness, NoCodeGameHarness
from .base import Problem, Entry

HARNESS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "harnesses")
CENTER = [3, 2, 4, 1, 5, 0, 6]


def _render(view) -> str:
    return (
        f"Connect 4. You are X, opponent is O. Top row is row 0; pieces fall down.\n"
        f"{view.render()}\n"
        f"Legal columns: {view.legal_moves}\n"
        "Reply ONLY with the column number you choose."
    )


def _parse(text, view):
    for tok in re.findall(r"\d", text or ""):
        if int(tok) in view.legal_moves:
            return int(tok)
    return None


def _guard(view):
    w = view.winning_move()
    if w is not None:
        return w
    return view.blocking_move()


def _fallback(view):
    for c in CENTER:
        if c in view.legal_moves:
            return c
    return view.legal_moves[0]


class Connect4Problem(Problem):
    slug = "connect4"
    title = "Connect 4: Head-to-Head"
    kind = "h2h"
    sponsor = "nebius"
    tagline = "Don't play the game. Engineer the agent that plays it."
    rules = [
        "Implement Harness.move(self, view, llm) -> column (0-6).",
        "Every harness plays every other harness twice (colors swapped).",
        "Win = 3 pts, Draw = 1, Loss = 0.",
        "Ties broken by efficiency: lower LLM cost, then fewer tokens.",
        "Crash / illegal move / timeout = you forfeit that game.",
    ]

    def template(self) -> str:
        with open(os.path.join(HARNESS_DIR, "_template.py"), encoding="utf-8") as f:
            return f.read()

    def baselines(self) -> list[Entry]:
        return [
            Entry("house-random", "RandomBot", "house", path=os.path.join(HARNESS_DIR, "random_bot.py")),
            Entry("house-heuristic", "HeuristicBot", "house", path=os.path.join(HARNESS_DIR, "heuristic_bot.py")),
            Entry("house-llm-naive", "LLM-Naive", "house", path=os.path.join(HARNESS_DIR, "llm_naive.py")),
            Entry("house-llm-strong", "LLM-Strong", "house", path=os.path.join(HARNESS_DIR, "llm_strong.py")),
        ]

    def make_harness(self, entry: Entry):
        if entry.is_nocode:
            return NoCodeGameHarness(entry.nocode, _render, _parse, _fallback, _guard)
        return load_code_harness(entry.path)

    def evaluate(self, entries: list[Entry]) -> dict:
        return run_tournament(entries, self.make_harness)

    def validate(self, entry: Entry) -> tuple[bool, str]:
        from engine.connect4 import Connect4, GameView
        from engine.llm import LLM
        try:
            h = self.make_harness(entry)
        except Exception as e:
            return False, f"failed to build harness: {type(e).__name__}: {e}"
        try:
            g = Connect4()
            col = h.move(GameView(g, me=1), LLM(model=getattr(h, "model", None)))
            if col not in g.legal_moves():
                return False, f"returned illegal column: {col!r}"
        except Exception as e:
            return False, f"crashed on first move: {type(e).__name__}: {e}"
        return True, ""
