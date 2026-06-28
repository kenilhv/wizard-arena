"""Connect-4 game engine and the GameView contract that harnesses receive."""
from __future__ import annotations
from copy import deepcopy
from typing import List, Optional

ROWS = 6
COLS = 7
EMPTY = 0


class Connect4:
    """Authoritative game state. board[r][c]: 0 empty, 1 player one, 2 player two.

    Row 0 is the TOP row; pieces fall to the largest available row index.
    """

    def __init__(self) -> None:
        self.board: List[List[int]] = [[EMPTY] * COLS for _ in range(ROWS)]
        self.turn: int = 1  # whose move it is (1 or 2)
        self.winner: Optional[int] = None  # 1, 2, or 0 for draw, None if ongoing
        self.move_history: List[int] = []

    # --- queries -------------------------------------------------------
    def legal_moves(self) -> List[int]:
        return [c for c in range(COLS) if self.board[0][c] == EMPTY]

    def is_over(self) -> bool:
        return self.winner is not None

    def landing_row(self, col: int) -> Optional[int]:
        for r in range(ROWS - 1, -1, -1):
            if self.board[r][col] == EMPTY:
                return r
        return None

    # --- mutation ------------------------------------------------------
    def play(self, col: int) -> None:
        if col not in self.legal_moves():
            raise ValueError(f"illegal move: {col}")
        r = self.landing_row(col)
        assert r is not None
        self.board[r][col] = self.turn
        self.move_history.append(col)
        if self._wins_at(r, col, self.turn):
            self.winner = self.turn
        elif not self.legal_moves():
            self.winner = 0  # draw
        else:
            self.turn = 3 - self.turn

    def _wins_at(self, r: int, c: int, p: int) -> bool:
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                rr, cc = r + dr * sign, c + dc * sign
                while 0 <= rr < ROWS and 0 <= cc < COLS and self.board[rr][cc] == p:
                    count += 1
                    rr += dr * sign
                    cc += dc * sign
            if count >= 4:
                return True
        return False

    def snapshot(self) -> List[List[int]]:
        return deepcopy(self.board)


class GameView:
    """Read-only view passed to a harness on each turn, with helpers."""

    def __init__(self, game: Connect4, me: int) -> None:
        self._board = game.snapshot()
        self.me: int = me
        self.opponent: int = 3 - me
        self.legal_moves: List[int] = game.legal_moves()
        self.last_move: Optional[int] = game.move_history[-1] if game.move_history else None
        self.move_number: int = len(game.move_history)

    @property
    def board(self) -> List[List[int]]:
        """6x7 grid, row 0 is top. 0=empty, your pieces == self.me."""
        return [row[:] for row in self._board]

    def _landing_row(self, col: int) -> Optional[int]:
        for r in range(ROWS - 1, -1, -1):
            if self._board[r][col] == EMPTY:
                return r
        return None

    def _would_win(self, col: int, player: int) -> bool:
        r = self._landing_row(col)
        if r is None:
            return False
        b = [row[:] for row in self._board]
        b[r][col] = player
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                rr, cc = r + dr * sign, col + dc * sign
                while 0 <= rr < ROWS and 0 <= cc < COLS and b[rr][cc] == player:
                    count += 1
                    rr += dr * sign
                    cc += dc * sign
            if count >= 4:
                return True
        return False

    def winning_move(self) -> Optional[int]:
        """A column that wins immediately for you, if any."""
        for c in self.legal_moves:
            if self._would_win(c, self.me):
                return c
        return None

    def blocking_move(self) -> Optional[int]:
        """A column you must play to stop the opponent winning next turn."""
        for c in self.legal_moves:
            if self._would_win(c, self.opponent):
                return c
        return None

    def render(self) -> str:
        """Human/LLM-readable board. '.' empty, 'X' you, 'O' opponent."""
        sym = {EMPTY: ".", self.me: "X", self.opponent: "O"}
        rows = ["".join(sym[v] for v in row) for row in self._board]
        header = "".join(str(c) for c in range(COLS))
        return header + "\n" + "\n".join(rows)
