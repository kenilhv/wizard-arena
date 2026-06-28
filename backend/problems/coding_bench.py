"""Coding Bench: agent harnesses write Python against hidden tests (CodingAgentBench DNA).

Harness contract:
    class Harness:
        def solve(self, spec: str, llm) -> str   # returns Python source
"""
from __future__ import annotations

import os
import re
import textwrap

from engine.llm import LLM
from engine.task_eval import run_task_board
from harness import load_code_harness
from harness_nocode_task import NoCodeCodingHarness
from .base import Problem, Entry

HARNESS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "harnesses")

TASKS = [
    {
        "id": "palindrome",
        "label": "Palindrome check",
        "spec": "Write a function `is_palindrome(s: str) -> bool` that returns True if s reads the same forwards and backwards (ignore case and non-alphanumeric).",
        "tests": [
            ("is_palindrome('racecar')", True),
            ("is_palindrome('A man a plan a canal Panama')", True),
            ("is_palindrome('hello')", False),
        ],
    },
    {
        "id": "fizzbuzz",
        "label": "FizzBuzz value",
        "spec": "Write `fizzbuzz(n: int) -> str` returning 'Fizz' if n divisible by 3, 'Buzz' if by 5, 'FizzBuzz' if both, else str(n).",
        "tests": [
            ("fizzbuzz(3)", "Fizz"),
            ("fizzbuzz(5)", "Buzz"),
            ("fizzbuzz(15)", "FizzBuzz"),
            ("fizzbuzz(7)", "7"),
        ],
    },
    {
        "id": "twosum",
        "label": "Two Sum indices",
        "spec": "Write `two_sum(nums: list[int], target: int) -> list[int]` returning indices of two numbers that add to target (exactly one solution, same element not twice).",
        "tests": [
            ("two_sum([2,7,11,15], 9)", [0, 1]),
            ("two_sum([3,2,4], 6)", [1, 2]),
        ],
    },
]


def _extract_code(raw: str) -> str:
    text = raw or ""
    fence = re.search(r"```(?:python)?\s*([\s\S]*?)```", text, re.I)
    if fence:
        return fence.group(1).strip()
    return text.strip()


def _run_tests(code: str, tests: list) -> tuple[int, int, str]:
    """Execute harness-produced code against visible-shape tests. Returns (passed, total, err)."""
    safe = {"__builtins__": {"range": range, "len": len, "str": str, "int": int, "list": list, "bool": bool}}
    ns: dict = {}
    try:
        exec(textwrap.dedent(code), safe, ns)  # noqa: S102 — intentional sandboxed eval for grading
    except Exception as e:
        return 0, len(tests), f"syntax/exec error: {type(e).__name__}: {e}"

    passed = 0
    last_err = ""
    for expr, expected in tests:
        try:
            got = eval(expr, safe, ns)  # noqa: S307
            if got == expected:
                passed += 1
            else:
                last_err = f"{expr} -> {got!r}, expected {expected!r}"
        except Exception as e:
            last_err = f"{expr} raised {type(e).__name__}: {e}"
    return passed, len(tests), last_err


class CodingBenchProblem(Problem):
    slug = "coding-bench"
    title = "Coding Bench"
    kind = "task"
    sponsor = "nebius"
    tagline = "Don't write the solution. Engineer the agent that does."
    rules = [
        "Implement Harness.solve(self, spec, llm) -> str (Python source).",
        "Graded on hidden tests — pass-rate primary, tokens-per-correct tiebreak.",
        "100 pts per fully-passing task; partial credit if some tests pass.",
        "Crash or invalid Python = 0 for that task.",
    ]
    supports_nocode = True

    def template(self) -> str:
        with open(os.path.join(HARNESS_DIR, "coding_template.py"), encoding="utf-8") as f:
            return f.read()

    def baselines(self) -> list[Entry]:
        return [
            Entry("house-coding-naive", "Coder-Naive", "house",
                  path=os.path.join(HARNESS_DIR, "coding_naive.py")),
            Entry("house-coding-strong", "Coder-Strong", "house",
                  path=os.path.join(HARNESS_DIR, "coding_strong.py")),
        ]

    def make_harness(self, entry: Entry):
        if entry.is_nocode:
            return NoCodeCodingHarness(entry.nocode)
        return load_code_harness(entry.path, method="solve")

    def evaluate(self, entries: list[Entry]) -> dict:
        def run_one(harness, task):
            llm = LLM(model=getattr(harness, "model", None))
            raw = harness.solve(task["spec"], llm)
            code = _extract_code(raw)
            passed, total, err = _run_tests(code, task["tests"])
            correct = passed == total
            usage = llm.usage.as_dict()
            return {
                "correct": correct,
                "detail": f"{passed}/{total} tests" + (f" — {err}" if err and not correct else ""),
                "usage": usage,
                "passed": passed,
                "total": total,
            }

        result = run_task_board(entries, self.make_harness, TASKS, run_one)
        for row in result["standings"]:
            entry_runs = [r for r in result["runs"] if r["entry_id"] == row["id"]]
            score = 0
            correct = 0
            for r in entry_runs:
                m = re.search(r"(\d+)/(\d+)", r.get("detail", ""))
                if m:
                    p, t = int(m.group(1)), int(m.group(2))
                    score += int(100 * p / t) if t else 0
                    if p == t:
                        correct += 1
            row["score"] = score
            row["points"] = score
            row["correct"] = correct
            row["accuracy"] = round(correct / row["total"], 3) if row["total"] else 0
        result["standings"] = sorted(
            result["standings"],
            key=lambda r: (-r["score"], r["cost_usd"], r["tokens"], r["latency_ms"]),
        )
        for i, row in enumerate(result["standings"], 1):
            row["rank"] = i
        return result

    def validate(self, entry: Entry) -> tuple[bool, str]:
        try:
            h = self.make_harness(entry)
        except Exception as e:
            return False, f"failed to build harness: {type(e).__name__}: {e}"
        try:
            code = _extract_code(h.solve(TASKS[0]["spec"], LLM(model=getattr(h, "model", None))))
            if not code.strip():
                return False, "returned empty code on smoke test"
            passed, total, err = _run_tests(code, TASKS[0]["tests"][:1])
            if passed == 0:
                return False, f"smoke test failed: {err}"
        except Exception as e:
            return False, f"crashed on smoke test: {type(e).__name__}: {e}"
        return True, ""
