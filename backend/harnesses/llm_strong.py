"""Reference 'good' harness. The point of the whole arena: a well-engineered
harness wraps the LLM with cheap deterministic guards and a structured prompt.

- Never spends a token on a forced move (immediate win / required block).
- Gives the model a clean board + explicit threat analysis, not raw mush.
- Always has a heuristic fallback, so a bad/garbled LLM reply never loses on a
  technicality.

It plays strong AND spends fewer tokens than the naive harness -- exactly the
trade-off the leaderboard rewards (win=3, ties broken by lower cost)."""
import re

CENTER_PREFERENCE = [3, 2, 4, 1, 5, 0, 6]


class Harness:
    name = "LLM-Strong"
    author = "house"

    def move(self, view, llm) -> int:
        # 1. Free, forced moves -- no LLM call needed.
        win = view.winning_move()
        if win is not None:
            return win
        block = view.blocking_move()
        if block is not None:
            return block

        # 2. Ask the model only for genuinely open positions, with structure.
        prompt = (
            "Connect 4. You are X, opponent is O. Top row is row 0; pieces fall "
            "down.\n"
            f"Board:\n{view.render()}\n"
            f"Legal columns: {view.legal_moves}\n"
            "Pick the column that builds your own threats and controls the "
            "center. Respond ONLY as: MOVE=<column>."
        )
        text = llm.chat(
            system="You are a world-class Connect 4 strategist. Be terse.",
            user=prompt,
            temperature=0.1,
            max_tokens=24,
        )

        m = re.search(r"MOVE\s*=\s*(\d)", text)
        if m and int(m.group(1)) in view.legal_moves:
            return int(m.group(1))
        for tok in re.findall(r"\d", text):
            if int(tok) in view.legal_moves:
                return int(tok)

        # 3. Deterministic fallback: center control.
        for col in CENTER_PREFERENCE:
            if col in view.legal_moves:
                return col
        return view.legal_moves[0]
