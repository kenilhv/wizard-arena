import { useEffect, useRef, useState, type ReactNode } from "react";
import { getMatch } from "../api";
import type { MatchDetail } from "../types";
import Board from "./Board";
import { IconSwords } from "./icons";

function reasonLabel(reason: string, winnerName: string): string {
  if (reason === "four_in_a_row") return `${winnerName} — four in a row!`;
  if (reason === "draw") return "Draw — board full";
  if (reason === "max_plies") return "Draw";
  if (reason.startsWith("forfeit_timeout")) return `${winnerName} wins — opponent timed out`;
  if (reason.startsWith("forfeit_illegal")) return `${winnerName} wins — opponent played illegally`;
  if (reason.startsWith("forfeit_error")) return `${winnerName} wins — opponent crashed`;
  return winnerName;
}

export default function ReplayModal({ id, onClose }: { id: string; onClose: () => void }) {
  const [m, setM] = useState<MatchDetail | null>(null);
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(550);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    getMatch(id).then((d) => {
      setM(d);
      setI(0);
      setPlaying(true);
    });
  }, [id]);

  useEffect(() => {
    if (!m || !playing) return;
    if (i >= m.frames.length - 1) {
      setPlaying(false);
      return;
    }
    timer.current = window.setTimeout(() => setI((x) => x + 1), speed);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [m, playing, i, speed]);

  if (!m) {
    return (
      <Overlay onClose={onClose}>
        <div className="p-10 text-center text-[var(--color-muted)]">Summoning replay…</div>
      </Overlay>
    );
  }

  const frame = m.frames[i];
  const atEnd = i >= m.frames.length - 1;
  const winnerName = m.winner === "draw" ? "Draw" : m.names[m.winner];

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-extrabold glow-text inline-flex items-center gap-2">
          <IconSwords size={20} /> Match Replay
        </h3>
        <button className="btn modal-close" onClick={onClose}>✕</button>
      </div>

      <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 items-center mb-4">
        <PlayerCard side="A" name={m.names.A} usage={m.usage.A} active={frame.mover === "A"} />
        <div className="text-center text-[var(--color-muted)] font-extrabold">VS</div>
        <PlayerCard side="B" name={m.names.B} usage={m.usage.B} active={frame.mover === "B"} />
      </div>

      <Board board={frame.board} lastMove={frame.move} />

      <div className="mt-4 text-center">
        {atEnd ? (
          <div className="text-lg font-extrabold gold-text">{reasonLabel(m.reason, winnerName)}</div>
        ) : (
          <div className="text-[var(--color-muted)]">
            move {i} / {m.frames.length - 1}
            {frame.move !== null && (
              <> — {frame.mover === "A" ? m.names.A : m.names.B} dropped column {frame.move}</>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
        <button className="btn" onClick={() => { setPlaying(false); setI(0); }}>⏮ Restart</button>
        <button className="btn" onClick={() => { setPlaying(false); setI((x) => Math.max(0, x - 1)); }}>◀ Step</button>
        {playing ? (
          <button className="btn btn-primary" onClick={() => setPlaying(false)}>⏸ Pause</button>
        ) : (
          <button
            className="btn btn-primary"
            onClick={() => { if (atEnd) setI(0); setPlaying(true); }}
          >▶ Play</button>
        )}
        <button className="btn" onClick={() => { setPlaying(false); setI((x) => Math.min(m.frames.length - 1, x + 1)); }}>Step ▶</button>
        <select
          className="btn"
          value={speed}
          onChange={(e) => setSpeed(Number(e.target.value))}
        >
          <option value={900}>0.5×</option>
          <option value={550}>1×</option>
          <option value={300}>2×</option>
          <option value={120}>4×</option>
        </select>
      </div>
    </Overlay>
  );
}

function Overlay({ children, onClose }: { children: ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(5,2,12,0.8)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div className="panel p-5 w-full max-w-2xl scroll" style={{ maxHeight: "92vh", overflowY: "auto" }} onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

function PlayerCard({
  side, name, usage, active,
}: { side: "A" | "B"; name: string; usage: MatchDetail["usage"]["A"]; active: boolean }) {
  const color = side === "A" ? "var(--color-cyan)" : "var(--color-amber)";
  return (
    <div
      className="panel p-3"
      style={{ boxShadow: active ? `0 0 18px ${color}66` : undefined, borderColor: active ? color : undefined }}
    >
      <div className="flex items-center gap-2">
        <span style={{ width: 14, height: 14, borderRadius: 99, background: color, display: "inline-block" }} />
        <span className="font-extrabold truncate">{name}</span>
      </div>
      <div className="text-xs text-[var(--color-muted)] mt-2 font-mono">
        {usage.calls} LLM calls · {usage.total_tokens} tok · ${usage.cost_usd.toFixed(6)}
      </div>
    </div>
  );
}
