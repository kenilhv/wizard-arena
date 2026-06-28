"""Harness loading: user code submissions and no-code (form-built) harnesses."""
from __future__ import annotations
import importlib.util
import uuid
from typing import Callable, Optional


def load_code_harness(path: str, method: str = "move"):
    """Import a user-submitted harness file and return an instantiated Harness()."""
    spec = importlib.util.spec_from_file_location(f"harness_{uuid.uuid4().hex}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load harness at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "Harness"):
        raise AttributeError(f"{path} does not define a `Harness` class")
    inst = module.Harness()
    if not hasattr(inst, method):
        raise AttributeError(f"{path}: Harness has no `{method}(...)` method")
    return inst


BASE_SYSTEM = (
    "You are an agent competing in a game. Follow the user's strategy notes and "
    "respond exactly in the requested format."
)


class NoCodeGameHarness:
    """A harness built from a form, not code: a chosen model + a system prompt +
    a few knobs. Game-specific behaviour comes from hooks the Problem supplies, so
    the same wrapper works for any turn-based game.

    config: {model, system_prompt, temperature, auto_guard, max_tokens}
    """

    def __init__(
        self,
        config: dict,
        render: Callable,                 # (view) -> str  user prompt
        parse: Callable,                  # (text, view) -> Optional[action]
        fallback: Callable,               # (view) -> action
        guard: Optional[Callable] = None  # (view) -> Optional[action] forced move
    ):
        self.model = config.get("model") or None
        self.system_prompt = (config.get("system_prompt") or "").strip()
        self.temperature = float(config.get("temperature", 0.2))
        self.max_tokens = int(config.get("max_tokens", 24))
        self.auto_guard = bool(config.get("auto_guard", True))
        self._render = render
        self._parse = parse
        self._fallback = fallback
        self._guard = guard

    def move(self, view, llm):
        if self.auto_guard and self._guard is not None:
            forced = self._guard(view)
            if forced is not None:
                return forced
        system = BASE_SYSTEM
        if self.system_prompt:
            system += "\n\nStrategy notes from the player:\n" + self.system_prompt
        text = llm.chat(
            system=system,
            user=self._render(view),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        action = self._parse(text, view)
        return action if action is not None else self._fallback(view)
