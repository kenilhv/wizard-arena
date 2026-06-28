"""Your harness. Implement move(self, view, llm) -> column (0-6).

`view` (read-only, this turn):
    view.board          6x7 grid, row 0 = top. 0 empty, your pieces == view.me
    view.me             your token (1 or 2);  view.opponent
    view.legal_moves    list of playable columns, e.g. [0,1,2,3,4,5,6]
    view.winning_move() a column that wins NOW, or None
    view.blocking_move()a column you must play to stop an opponent win, or None
    view.render()       ASCII board ('X'=you, 'O'=opp) -- great for prompting

`llm` (metered -- fewer tokens breaks ties in your favor):
    llm.chat(system, user, temperature=0.2, max_tokens=256) -> str

Rules: return an illegal column / crash / time out  =>  you forfeit that game.
Tip: handle forced moves yourself, only call the LLM when it actually matters.
"""


class Harness:
    name = "MyHarness"      # shown on the leaderboard
    author = "your-name"

    def move(self, view, llm) -> int:
        win = view.winning_move()
        if win is not None:
            return win
        block = view.blocking_move()
        if block is not None:
            return block

        # ---- your spell goes here -------------------------------------
        # Example: ask the model, then fall back to a safe default.
        reply = llm.chat(
            system="You are a Connect 4 expert. Answer with one column number.",
            user=f"You are X.\n{view.render()}\nLegal: {view.legal_moves}",
            max_tokens=16,
        )
        for ch in reply:
            if ch.isdigit() and int(ch) in view.legal_moves:
                return int(ch)
        return view.legal_moves[0]
