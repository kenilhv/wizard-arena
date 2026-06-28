import type { Contest } from "../types";
import { Dot } from "./icons";

function fmt(ts: number) {
  return new Date(ts * 1000).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

export default function ContestBar({
  contests, selected, onSelect, problemSlug,
}: {
  contests: Contest[];
  selected: string | null;
  onSelect: (id: string | null) => void;
  problemSlug: string;
}) {
  const relevant = contests.filter((c) => c.problem_slug === problemSlug);

  return (
    <div className="flex flex-wrap items-center gap-2 mt-3">
      <span className="text-xs font-bold uppercase tracking-wide text-[var(--color-muted)]">Mode</span>
      <button className={`tab ${!selected ? "active" : ""}`} onClick={() => onSelect(null)}>
        Practice
      </button>
      {relevant.map((c) => (
        <button
          key={c.id}
          className={`tab inline-flex items-center gap-1.5 ${selected === c.id ? "active" : ""}`}
          onClick={() => onSelect(c.id)}
          title={`${fmt(c.start_at)} – ${fmt(c.end_at)}`}
        >
          <Dot color={c.is_open ? "#fb7185" : c.is_upcoming ? "#22d3ee" : "#8b7db0"} />
          {c.is_open ? "LIVE · " : c.is_upcoming ? "Soon · " : ""}{c.title}
        </button>
      ))}
      {relevant.length === 0 && (
        <span className="text-xs text-[var(--color-muted)]">No contests for this problem yet</span>
      )}
    </div>
  );
}
