interface Props {
  board: number[][];
  lastMove: number | null;
}

/** Renders a 6x7 Connect-4 board. value 1 = player A (cyan), 2 = player B (amber). */
export default function Board({ board, lastMove }: Props) {
  // The most recently dropped disc in a column is the topmost filled cell.
  let lastRow = -1;
  if (lastMove !== null) {
    for (let r = 0; r < board.length; r++) {
      if (board[r][lastMove] !== 0) {
        lastRow = r;
        break;
      }
    }
  }
  return (
    <div className="board-grid">
      {board.map((row, r) =>
        row.map((v, c) => (
          <div
            key={`${r}-${c}`}
            className={`cell${lastMove === c && lastRow === r ? " last" : ""}`}
          >
            {v === 1 && <div className="disc-a" />}
            {v === 2 && <div className="disc-b" />}
          </div>
        ))
      )}
    </div>
  );
}
