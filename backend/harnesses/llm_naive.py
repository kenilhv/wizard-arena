"""Baseline harness: naive LLM use. Dumps the board, asks for a column, plays
whatever it parses. No safety net beyond legality -- demonstrates that *calling*
an LLM is not the same as engineering a good harness. Burns tokens, plays mediocre."""
import re
import random


class Harness:
    name = "LLM-Naive"
    author = "house"

    def move(self, view, llm) -> int:
        prompt = (
            f"Connect 4 board (you are X):\n{view.render()}\n"
            f"Legal columns: {view.legal_moves}. Reply with just the column number."
        )
        text = llm.chat(system="You play Connect 4.", user=prompt, max_tokens=16)
        for tok in re.findall(r"\d", text):
            col = int(tok)
            if col in view.legal_moves:
                return col
        return random.choice(view.legal_moves)
