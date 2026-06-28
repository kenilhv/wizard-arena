"""Score task-style problems (research, coding bench). Each entry runs
independently; ranking is by score then efficiency (CodingAgentBench-style)."""
from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List


def _blank_row(entry) -> Dict[str, Any]:
    return {
        "id": entry.id,
        "name": entry.name,
        "author": entry.author,
        "mode": "nocode" if entry.is_nocode else "code",
        "score": 0,
        "correct": 0,
        "total": 0,
        "accuracy": 0.0,
        "tokens": 0,
        "cost_usd": 0.0,
        "search_queries": 0,
        "latency_ms": 0,
        "forfeits": 0,
        # h2h fields zeroed so one Standing shape works in the UI
        "points": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "games": 0,
    }


def run_task_board(
    entries: List,
    make_harness: Callable,
    tasks: List[dict],
    run_one: Callable,
) -> Dict[str, Any]:
    """run_one(harness, task) -> {correct: bool, detail: str, usage: dict}"""
    table: Dict[str, Dict[str, Any]] = {e.id: _blank_row(e) for e in entries}
    runs: List[Dict[str, Any]] = []

    for entry in entries:
        harness = make_harness(entry)
        row = table[entry.id]
        t0 = time.perf_counter()
        for task in tasks:
            rid = uuid.uuid4().hex[:12]
            try:
                outcome = run_one(harness, task)
                correct = bool(outcome.get("correct"))
                usage = outcome.get("usage") or {}
            except Exception as e:
                correct = False
                usage = {}
                outcome = {"detail": f"crashed:{type(e).__name__}", "error": str(e)}
                row["forfeits"] += 1

            row["total"] += 1
            row["correct"] += int(correct)
            row["tokens"] += int(usage.get("total_tokens", 0))
            row["cost_usd"] = round(row["cost_usd"] + float(usage.get("cost_usd", 0)), 6)
            row["search_queries"] += int(usage.get("search_queries", 0))

            runs.append({
                "id": rid,
                "entry_id": entry.id,
                "entry_name": entry.name,
                "task_id": task.get("id"),
                "task_label": task.get("label") or task.get("id"),
                "correct": correct,
                "detail": outcome.get("detail", ""),
                "usage": usage,
            })

        elapsed = int((time.perf_counter() - t0) * 1000)
        row["latency_ms"] = elapsed
        row["accuracy"] = round(row["correct"] / row["total"], 3) if row["total"] else 0.0
        # Primary score: 100 pts per correct answer
        row["score"] = row["correct"] * 100
        row["points"] = row["score"]

    standings = sorted(
        table.values(),
        key=lambda r: (-r["score"], r["cost_usd"], r["tokens"], r["latency_ms"]),
    )
    for i, row in enumerate(standings, 1):
        row["rank"] = i
    return {"kind": "task", "standings": standings, "runs": runs}
