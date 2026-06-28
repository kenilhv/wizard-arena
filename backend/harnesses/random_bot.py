"""Baseline harness: plays a random legal move. The floor of the leaderboard."""
import random


class Harness:
    name = "RandomBot"
    author = "house"

    def move(self, view, llm) -> int:
        return random.choice(view.legal_moves)
