"""Metered LLM client handed to each harness.

Wraps Nebius (OpenAI-compatible) chat completions and records token usage and a
nominal cost so the tournament can rank harnesses on efficiency, not just wins.
Falls back to a deterministic mock when NEBIUS_API_KEY is absent, so the whole
arena runs offline (e.g. on stage with no wifi).
"""
from __future__ import annotations
import os
import hashlib
import httpx
from dataclasses import dataclass, field

NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1")
# Default: fast MoE (3B active) — good for many calls in a live tournament.
DEFAULT_MODEL = os.getenv("NEBIUS_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")

# Nominal price per 1M tokens (USD). Used only for relative ranking / display.
PRICE_PER_MTOK = float(os.getenv("NEBIUS_PRICE_PER_MTOK", "0.13"))

# Models selectable in the no-code harness builder (Nebius-hosted, verified live).
AVAILABLE_MODELS = [
    {"id": "Qwen/Qwen3-30B-A3B-Instruct-2507", "label": "Qwen3 30B (fast MoE, cheap)"},
    {"id": "meta-llama/Llama-3.3-70B-Instruct", "label": "Llama 3.3 70B (balanced)"},
    {"id": "openai/gpt-oss-120b", "label": "GPT-OSS 120B (strong)"},
    {"id": "deepseek-ai/DeepSeek-V4-Pro", "label": "DeepSeek V4 Pro (frontier)"},
    {"id": "mock", "label": "Mock (offline, free)"},
]


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        return round(self.total_tokens / 1_000_000 * PRICE_PER_MTOK, 6)

    def as_dict(self) -> dict:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }


class LLM:
    """Per-harness LLM handle. One instance per harness per match so usage is
    attributed to the right competitor."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or DEFAULT_MODEL
        self.api_key = api_key if api_key is not None else os.getenv("NEBIUS_API_KEY", "")
        self.usage = Usage()
        # No key -> mock. Model "mock" forces offline even when a key is present.
        self.mock = (not bool(self.api_key)) or self.model == "mock"

    def chat(self, system: str, user: str, temperature: float = 0.2,
             max_tokens: int = 256) -> str:
        """Single-turn chat. Returns the assistant text. Metered."""
        self.usage.calls += 1
        if self.mock:
            return self._mock(system, user, max_tokens)
        try:
            resp = httpx.post(
                f"{NEBIUS_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            u = data.get("usage", {})
            self.usage.prompt_tokens += int(u.get("prompt_tokens", 0))
            self.usage.completion_tokens += int(u.get("completion_tokens", 0))
            return data["choices"][0]["message"]["content"] or ""
        except Exception as e:  # network/key/rate errors must not crash a match
            self.usage.prompt_tokens += _est_tokens(system + user)
            return f"[llm-error:{type(e).__name__}]"

    # --- deterministic offline mock -----------------------------------
    def _mock(self, system: str, user: str, max_tokens: int) -> str:
        self.usage.prompt_tokens += _est_tokens(system + user)
        # Deterministic pseudo-answer; harnesses are expected to have a fallback
        # so a weak mock simply means LLM harnesses lean on their own logic.
        h = hashlib.sha256((system + "||" + user).encode()).hexdigest()
        digit = str(int(h[:8], 16) % 7)
        out = f"I'll play column {digit}."
        self.usage.completion_tokens += _est_tokens(out)
        return out


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)
