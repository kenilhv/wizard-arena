"""Problem registry. Add new problems here to give them a leaderboard."""
from .base import Problem, Entry
from .connect4 import Connect4Problem
from .research_agent import ResearchAgentProblem
from .coding_bench import CodingBenchProblem

_PROBLEMS = [Connect4Problem(), ResearchAgentProblem(), CodingBenchProblem()]
REGISTRY: dict[str, Problem] = {p.slug: p for p in _PROBLEMS}


def get_problem(slug: str) -> Problem | None:
    return REGISTRY.get(slug)


def list_problems() -> list[Problem]:
    return list(REGISTRY.values())
