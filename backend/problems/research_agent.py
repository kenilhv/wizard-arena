"""Research Agent: answer hidden factual questions using live web search (You.com).

Harness contract:
    class Harness:
        def research(self, question: str, search, llm) -> str
"""
from __future__ import annotations

import os
import re

from engine.llm import LLM
from engine.search import SearchClient
from engine.task_eval import run_task_board
from harness import load_code_harness
from harness_nocode_task import NoCodeResearchHarness
from .base import Problem, Entry

HARNESS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "harnesses")

# Hidden task suite — competitors never see answers, only labels in replays.
TASKS = [
    {"id": "q1", "label": "GPT-4 release", "question": "In what year did OpenAI publicly release GPT-4?",
     "answers": ["2023", "twenty twenty-three"]},
    {"id": "q2", "label": "Python creator", "question": "Who created the Python programming language?",
     "answers": ["guido van rossum", "rossum"]},
    {"id": "q3", "label": "Nebius domain", "question": "What does Nebius provide for AI developers?",
     "answers": ["cloud", "infrastructure", "ai cloud", "gpu", "full-stack"]},
    {"id": "q4", "label": "Connect Four", "question": "What kind of game is Connect Four?",
     "answers": ["board", "connection", "strategy", "two-player", "grid"]},
    {"id": "q5", "label": "InsForge", "question": "What type of platform is InsForge?",
     "answers": ["backend", "agent-native", "baas", "cloud", "infrastructure"]},
]


def _grade(answer: str, task: dict) -> bool:
    text = re.sub(r"[^\w\s]", " ", (answer or "").lower())
    text = " ".join(text.split())
    for accept in task["answers"]:
        if accept.lower() in text:
            return True
    return False


class ResearchAgentProblem(Problem):
    slug = "research-agent"
    title = "Research Agent"
    kind = "task"
    sponsor = "you.com"
    tagline = "Don't memorize facts. Engineer the agent that finds them."
    rules = [
        "Implement Harness.research(self, question, search, llm) -> str.",
        "search.search(query) returns web snippets (You.com). llm.chat() for synthesis.",
        "Scored on hidden questions: 100 pts each correct answer.",
        "Tiebreak: lower LLM cost → fewer tokens → faster → fewer searches.",
        "Crash or empty answer = wrong for that question.",
    ]
    supports_nocode = True

    def template(self) -> str:
        with open(os.path.join(HARNESS_DIR, "research_template.py"), encoding="utf-8") as f:
            return f.read()

    def baselines(self) -> list[Entry]:
        return [
            Entry("house-research-naive", "Search-Naive", "house",
                  path=os.path.join(HARNESS_DIR, "research_naive.py")),
            Entry("house-research-strong", "Search-Strong", "house",
                  path=os.path.join(HARNESS_DIR, "research_strong.py")),
        ]

    def make_harness(self, entry: Entry):
        if entry.is_nocode:
            return NoCodeResearchHarness(entry.nocode)
        return load_code_harness(entry.path, method="research")

    def evaluate(self, entries: list[Entry]) -> dict:
        def run_one(harness, task):
            search = SearchClient()
            llm = LLM(model=getattr(harness, "model", None))
            answer = harness.research(task["question"], search, llm)
            correct = _grade(answer, task)
            usage = llm.usage.as_dict()
            usage["search_queries"] = search.usage.queries
            return {
                "correct": correct,
                "detail": answer[:200],
                "usage": usage,
            }

        return run_task_board(entries, self.make_harness, TASKS, run_one)

    def validate(self, entry: Entry) -> tuple[bool, str]:
        from engine.llm import LLM
        from engine.search import SearchClient
        try:
            h = self.make_harness(entry)
        except Exception as e:
            return False, f"failed to build harness: {type(e).__name__}: {e}"
        try:
            ans = h.research(TASKS[0]["question"], SearchClient(), LLM(model=getattr(h, "model", None)))
            if not (ans or "").strip():
                return False, "returned empty answer on smoke test"
        except Exception as e:
            return False, f"crashed on smoke test: {type(e).__name__}: {e}"
        return True, ""
