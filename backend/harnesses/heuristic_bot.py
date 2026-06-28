"""Baseline harness: pure rules, no LLM. Win if you can, block if you must,
otherwise prefer the center. Cheap (zero tokens) and surprisingly tough -- the
bar that LLM harnesses must beat to justify their cost."""

CENTER_PREFERENCE = [3, 2, 4, 1, 5, 0, 6]


class Harness:
    name = "HeuristicBot"
    author = "house"

    def move(self, view, llm) -> int:
        win = view.winning_move()
        if win is not None:
            return win
        block = view.blocking_move()
        if block is not None:
            return block
        for col in CENTER_PREFERENCE:
            if col in view.legal_moves:
                return col
        return view.legal_moves[0]
