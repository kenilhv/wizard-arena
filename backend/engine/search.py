"""Metered web-search client handed to research harnesses.

Provider-aware: prefers Tavily (Nebius-aligned), then You.com, then a
deterministic offline mock so the arena still runs with no wifi (e.g. on stage).
The selected provider is recorded so leaderboards/health can show which engine
powered a run.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import httpx

YOU_SEARCH_URL = os.getenv("YOU_SEARCH_URL", "https://ydc-index.io/v1/search")
TAVILY_SEARCH_URL = os.getenv("TAVILY_SEARCH_URL", "https://api.tavily.com/search")


def active_provider() -> str:
    """Which search engine the arena will use, given the configured keys."""
    if os.getenv("TAVILY_API_KEY"):
        return "tavily"
    if os.getenv("YOU_API_KEY"):
        return "you.com"
    return "mock"


@dataclass
class SearchUsage:
    queries: int = 0
    provider: str = "mock"

    def as_dict(self) -> dict:
        return {"queries": self.queries, "provider": self.provider}


# Curated mock snippets keyed by question hash — enough for offline grading.
_MOCK_SNIPPETS: dict[str, list[str]] = {
    "gpt4": ["OpenAI released GPT-4 on March 14, 2023."],
    "python": ["Python was created by Guido van Rossum and first released in 1991."],
    "nebius": ["Nebius provides full-stack AI cloud infrastructure for developers."],
    "connect4": ["Connect Four is a two-player connection board game invented by Howard Wexler."],
    "insforge": ["InsForge is an agent-native cloud infrastructure platform with Postgres, auth, and storage."],
    "tavily": ["Tavily is a search API built for AI agents and LLM grounding."],
}


class SearchClient:
    """Per-harness search handle. One instance per run so query counts attribute.

    `provider` can be forced ("tavily" | "you.com" | "mock"); otherwise it is
    auto-selected from available API keys.
    """

    def __init__(self, api_key: str | None = None, provider: str | None = None):
        self.provider = provider or active_provider()
        if api_key is not None:
            self.api_key = api_key
        elif self.provider == "tavily":
            self.api_key = os.getenv("TAVILY_API_KEY", "")
        elif self.provider == "you.com":
            self.api_key = os.getenv("YOU_API_KEY", "")
        else:
            self.api_key = ""
        if not self.api_key:
            self.provider = "mock"
        self.usage = SearchUsage(provider=self.provider)
        self.mock = self.provider == "mock"

    def search(self, query: str, count: int = 5) -> str:
        """Return a compact text block of search snippets for the harness/LLM."""
        self.usage.queries += 1
        if self.mock:
            return self._mock(query, count)
        try:
            if self.provider == "tavily":
                return self._tavily(query, count)
            return self._youcom(query, count)
        except Exception as e:
            return f"[search-error:{type(e).__name__}] No results."

    def _tavily(self, query: str, count: int) -> str:
        resp = httpx.post(
            TAVILY_SEARCH_URL,
            headers={"Content-Type": "application/json"},
            json={
                "api_key": self.api_key,
                "query": query,
                "max_results": count,
                "search_depth": "basic",
                "include_answer": True,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        lines: list[str] = []
        answer = data.get("answer")
        if answer:
            lines.append(f"- Answer: {answer}")
        for item in data.get("results", []) or []:
            title = item.get("title") or "Result"
            content = (item.get("content") or "").strip()
            url = item.get("url") or ""
            lines.append(f"- {title}: {content} ({url})".strip())
        return "\n".join(lines[:12]) or "No results found."

    def _youcom(self, query: str, count: int) -> str:
        resp = httpx.get(
            YOU_SEARCH_URL,
            headers={"X-API-Key": self.api_key},
            params={"query": query, "count": count},
            timeout=20.0,
        )
        resp.raise_for_status()
        return self._format_youcom(resp.json())

    def _format_youcom(self, data: dict) -> str:
        lines: list[str] = []
        for section in ("web", "news"):
            for item in (data.get("results") or {}).get(section, []) or []:
                title = item.get("title") or item.get("name") or "Result"
                desc = item.get("description") or item.get("snippet") or ""
                url = item.get("url") or item.get("link") or ""
                lines.append(f"- {title}: {desc} ({url})".strip())
        return "\n".join(lines[:12]) or "No results found."

    def _mock(self, query: str, count: int) -> str:
        q = (query or "").lower()
        for key, snippets in _MOCK_SNIPPETS.items():
            if key in q:
                return "\n".join(f"- Mock result: {s}" for s in snippets[:count])
        h = hashlib.sha256(query.encode()).hexdigest()[:6]
        return f"- Mock search [{h}]: synthetic snippet for '{query[:60]}'"
