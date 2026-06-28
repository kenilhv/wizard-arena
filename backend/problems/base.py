"""Problem abstraction: every challenge (game or task) implements this so the
platform can host many problems, each with its own leaderboard."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Entry:
    """A competitor in a problem: either a code harness file or a no-code config."""
    id: str
    name: str
    author: str = "anon"
    path: Optional[str] = None          # code submission: path to a .py file
    nocode: Optional[dict] = None       # no-code config: {model, system_prompt, ...}

    @property
    def is_nocode(self) -> bool:
        return self.nocode is not None


class Problem:
    """Base class. h2h problems run a tournament; task problems score each entry
    independently. Subclasses implement `evaluate`."""

    slug: str = ""
    title: str = ""
    kind: str = "h2h"                    # "h2h" | "task"
    sponsor: str = "nebius"              # primary sponsor tech for this problem
    tagline: str = ""
    rules: list[str] = []
    supports_nocode: bool = True

    def template(self) -> str:
        """Starter code shown in the submit editor."""
        raise NotImplementedError

    def baselines(self) -> list[Entry]:
        """House entries that seed this problem's leaderboard."""
        return []

    def make_harness(self, entry: Entry):
        """Build a FRESH harness instance for one run (no cross-run state)."""
        raise NotImplementedError

    def evaluate(self, entries: list[Entry]) -> dict:
        """Return {kind, standings: [...], runs: [...]} for the given entries."""
        raise NotImplementedError

    def validate(self, entry: Entry) -> tuple[bool, str]:
        """Cheap self-check that an entry runs. Override per problem."""
        return True, ""

    def meta(self) -> dict:
        return {
            "slug": self.slug, "title": self.title, "kind": self.kind,
            "sponsor": self.sponsor, "tagline": self.tagline, "rules": self.rules,
            "supports_nocode": self.supports_nocode,
        }
