"""No-code harness for research / task problems: model + system prompt + search loop."""
from __future__ import annotations

from typing import Callable, Optional

from engine.llm import LLM
from engine.search import SearchClient

BASE_RESEARCH_SYSTEM = (
    "You are a research agent. Use the provided web search results to answer "
    "factual questions accurately and concisely. Reply with ONLY the answer — no preamble."
)


class NoCodeResearchHarness:
    """Form-built research harness: searches, then asks the LLM to synthesize."""

    def __init__(self, config: dict):
        self.model = config.get("model") or None
        self.system_prompt = (config.get("system_prompt") or "").strip()
        self.temperature = float(config.get("temperature", 0.1))
        self.max_tokens = int(config.get("max_tokens", 64))
        self.search_depth = int(config.get("search_depth", 5))

    def research(self, question: str, search: SearchClient, llm: LLM) -> str:
        snippets = search.search(question, count=self.search_depth)
        system = BASE_RESEARCH_SYSTEM
        if self.system_prompt:
            system += "\n\nStrategy notes:\n" + self.system_prompt
        user = (
            f"Question: {question}\n\n"
            f"Web search results:\n{snippets}\n\n"
            "Answer concisely:"
        )
        return llm.chat(system=system, user=user, temperature=self.temperature, max_tokens=self.max_tokens)


class NoCodeCodingHarness:
    """Form-built coding harness: LLM writes Python for a given spec."""

    def __init__(self, config: dict):
        self.model = config.get("model") or None
        self.system_prompt = (config.get("system_prompt") or "").strip()
        self.temperature = float(config.get("temperature", 0.0))
        self.max_tokens = int(config.get("max_tokens", 512))

    def solve(self, spec: str, llm: LLM) -> str:
        system = (
            "You write Python solutions for coding tasks. Return ONLY valid Python code "
            "with no markdown fences, no explanation."
        )
        if self.system_prompt:
            system += "\n\nStrategy notes:\n" + self.system_prompt
        user = f"Task:\n{spec}\n\nWrite the solution as a Python function or module:"
        return llm.chat(system=system, user=user, temperature=self.temperature, max_tokens=self.max_tokens)
