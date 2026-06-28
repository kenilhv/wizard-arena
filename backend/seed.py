"""House harnesses that seed the leaderboard so the arena is never empty."""
import os

HARNESS_DIR = os.path.join(os.path.dirname(__file__), "harnesses")

BASELINES = [
    {"id": "house-random", "name": "RandomBot", "author": "house",
     "path": os.path.join(HARNESS_DIR, "random_bot.py")},
    {"id": "house-heuristic", "name": "HeuristicBot", "author": "house",
     "path": os.path.join(HARNESS_DIR, "heuristic_bot.py")},
    {"id": "house-llm-naive", "name": "LLM-Naive", "author": "house",
     "path": os.path.join(HARNESS_DIR, "llm_naive.py")},
    {"id": "house-llm-strong", "name": "LLM-Strong", "author": "house",
     "path": os.path.join(HARNESS_DIR, "llm_strong.py")},
]
