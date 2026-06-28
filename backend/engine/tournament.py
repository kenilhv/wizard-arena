"""Round-robin tournament for head-to-head game problems. Every entry plays every
other twice (colors swapped). Ranking: points (win=3, draw=1), then efficiency --
lower LLM cost, then fewer tokens."""
from __future__ import annotations
from itertools import combinations
from typing import Any, Callable, Dict, List

from .runner import play_match

WIN, DRAW, LOSS = 3, 1, 0


def _blank_row(entry) -> Dict[str, Any]:
    return {
        "id": entry.id, "name": entry.name, "author": entry.author,
        "mode": "nocode" if entry.is_nocode else "code",
        "points": 0, "wins": 0, "draws": 0, "losses": 0, "games": 0,
        "tokens": 0, "cost_usd": 0.0, "forfeits": 0,
    }


def run_tournament(entries: List, make_harness: Callable) -> Dict[str, Any]:
    """entries: list[Entry]; make_harness: Entry -> fresh harness instance."""
    table: Dict[str, Dict[str, Any]] = {e.id: _blank_row(e) for e in entries}
    matches: List[Dict[str, Any]] = []

    def record(eid: str, outcome: int, usage: Dict[str, Any], forfeited: bool):
        row = table[eid]
        row["points"] += outcome
        row["games"] += 1
        row["wins"] += outcome == WIN
        row["draws"] += outcome == DRAW
        row["losses"] += outcome == LOSS
        row["tokens"] += usage["total_tokens"]
        row["cost_usd"] = round(row["cost_usd"] + usage["cost_usd"], 6)
        row["forfeits"] += forfeited

    for a, b in combinations(entries, 2):
        for first, second in ((a, b), (b, a)):
            m = play_match(make_harness(first), first.name, make_harness(second), second.name)
            m["entry_ids"] = {"A": first.id, "B": second.id}
            forfeit = str(m["reason"]).startswith("forfeit")
            if m["winner"] == "A":
                record(first.id, WIN, m["usage"]["A"], False)
                record(second.id, LOSS, m["usage"]["B"], forfeit)
            elif m["winner"] == "B":
                record(first.id, LOSS, m["usage"]["A"], forfeit)
                record(second.id, WIN, m["usage"]["B"], False)
            else:
                record(first.id, DRAW, m["usage"]["A"], False)
                record(second.id, DRAW, m["usage"]["B"], False)
            matches.append(m)

    standings = sorted(table.values(), key=lambda r: (-r["points"], r["cost_usd"], r["tokens"], -r["wins"]))
    for i, row in enumerate(standings, 1):
        row["rank"] = i
    return {"kind": "h2h", "standings": standings, "runs": matches}
