import type { Leaderboard as LB, MatchSummary, TaskRunSummary } from "../types";
import { IconTrophy, IconSwords, IconTerminal } from "./icons";

const maxScore = (s: LB["standings"]) =>
  Math.max(1, ...s.map((r) => (r.score ?? r.points) || 0));

const MEDAL_BG: Record<number, string> = {
  1: "linear-gradient(180deg,#fcd34d,#d99e2b)",
  2: "linear-gradient(180deg,#e5e7eb,#9ca3af)",
  3: "linear-gradient(180deg,#e0a878,#b4703c)",
};

function RankBadge({ rank }: { rank: number }) {
  if (rank <= 3) {
    return (
      <span className="grid place-items-center font-black"
        style={{ width: 28, height: 28, borderRadius: 999, background: MEDAL_BG[rank],
          color: "#1a1100", fontSize: "0.9rem" }}>
        {rank}
      </span>
    );
  }
  return <span className="text-[var(--color-muted)] font-bold">{rank}</span>;
}

function outcomeText(m: MatchSummary): { text: string } {
  if (m.winner === "draw") return { text: `${m.name_a} vs ${m.name_b} — draw` };
  const w = m.winner === "A" ? m.name_a : m.name_b;
  const l = m.winner === "A" ? m.name_b : m.name_a;
  const how = m.reason.startsWith("forfeit") ? " (forfeit)" : "";
  return { text: `${w} beat ${l}${how}` };
}

function sponsorBadge(sponsor: string) {
  const map: Record<string, string> = {
    "nebius": "Nebius",
    "you.com": "You.com",
    "insforge": "InsForge",
  };
  return map[sponsor] || sponsor;
}

export default function Leaderboard({
  data, onWatch, sponsor,
}: { data: LB; onWatch: (id: string) => void; sponsor?: string }) {
  const isTask = data.kind === "task";
  const max = maxScore(data.standings);
  const runs = data.task_runs || [];

  return (
    <div className="grid gap-5 @3xl:grid-cols-[1.5fr_minmax(0,1fr)]">
      <div className="panel p-5 min-w-0">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-extrabold glow-text inline-flex items-center gap-2">
            <IconTrophy size={18} /> Arena Standings
          </h2>
          <div className="flex gap-2">
            {sponsor && <span className="badge gold-text">{sponsorBadge(sponsor)}</span>}
            <span className="badge">{data.standings.length} harnesses</span>
          </div>
        </div>
        <div className="scroll" style={{ overflowX: "auto" }}>
        <table className="lb" style={{ minWidth: isTask ? 520 : 440 }}>
          <thead>
            <tr>
              <th>#</th>
              <th>Harness</th>
              <th>{isTask ? "Score" : "Pts"}</th>
              {isTask ? (
                <>
                  <th>Acc</th>
                  <th>Searches</th>
                  <th>Latency</th>
                </>
              ) : (
                <th>W-D-L</th>
              )}
              <th>Tokens</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {data.standings.map((r) => {
              const score = r.score ?? r.points;
              return (
              <tr key={r.id}>
                <td><RankBadge rank={r.rank} /></td>
                <td>
                  <div className="font-bold flex items-center gap-2 flex-wrap">
                    {r.name}
                    {r.mode === "nocode"
                      ? <span className="badge" style={{ color: "var(--color-cyan)", borderColor: "var(--color-cyan)" }}>no-code</span>
                      : <span className="badge">code</span>}
                    {r.author === "house" && <span className="badge badge-house">house</span>}
                  </div>
                  <div className="text-xs text-[var(--color-muted)]">by {r.author}</div>
                  <div className="bar mt-1" style={{ width: 160 }}>
                    <div style={{ width: `${(score / max) * 100}%` }} />
                  </div>
                </td>
                <td className="font-extrabold" style={{ fontSize: "1.1rem" }}>{score}</td>
                {isTask ? (
                  <>
                    <td className="font-mono text-sm">
                      {r.correct ?? 0}/{r.total ?? 0}
                      <span className="text-[var(--color-muted)]"> ({((r.accuracy ?? 0) * 100).toFixed(0)}%)</span>
                    </td>
                    <td className="font-mono text-sm text-[var(--color-muted)]">{r.search_queries ?? 0}</td>
                    <td className="font-mono text-sm text-[var(--color-muted)]">{r.latency_ms ?? 0}ms</td>
                  </>
                ) : (
                  <td className="font-mono text-sm">
                    <span style={{ color: "var(--color-cyan)" }}>{r.wins}</span>-
                    {r.draws}-
                    <span style={{ color: "var(--color-amber)" }}>{r.losses}</span>
                    {r.forfeits > 0 && (
                      <span className="text-[var(--color-muted)]"> · {r.forfeits} ff</span>
                    )}
                  </td>
                )}
                <td className="font-mono text-sm text-[var(--color-muted)]">
                  {r.tokens.toLocaleString()}
                </td>
                <td className="font-mono text-sm gold-text">${r.cost_usd.toFixed(5)}</td>
              </tr>
            );})}
          </tbody>
        </table>
        </div>
        <p className="text-xs text-[var(--color-muted)] mt-4">
          {isTask
            ? "Ranked by score (correct answers / test pass-rate). Ties broken by cost → tokens → latency → searches."
            : "Ranked by points (win 3 · draw 1). Ties broken by efficiency — lowest LLM cost, then fewest tokens."}
        </p>
      </div>

      <div className="panel p-5 min-w-0">
        <h2 className="text-lg font-extrabold glow-text mb-4 inline-flex items-center gap-2">
          {isTask ? <IconTerminal size={18} /> : <IconSwords size={18} />}
          {isTask ? "Task Results" : "Recent Battles"}
        </h2>
        <div className="scroll" style={{ maxHeight: 520, overflowY: "auto" }}>
          {isTask ? (
            runs.length === 0 ? (
              <div className="text-[var(--color-muted)] text-sm">No runs yet — run evaluation.</div>
            ) : (
              runs.slice().reverse().slice(0, 40).map((r: TaskRunSummary) => (
                <div key={r.id} className="mb-2 p-2 rounded-lg"
                  style={{ background: "var(--color-panel2)", border: "1px solid var(--color-border)" }}>
                  <div className="text-sm font-semibold flex justify-between gap-2">
                    <span>{r.entry_name} · {r.task_label}</span>
                    <span style={{ color: r.correct ? "var(--color-cyan)" : "#fb7185" }}>
                      {r.correct ? "✓" : "✗"}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--color-muted)] truncate">{r.detail}</div>
                </div>
              ))
            )
          ) : (
            <>
              {data.matches.length === 0 && (
                <div className="text-[var(--color-muted)] text-sm">No matches yet — run the tournament.</div>
              )}
              {data.matches.map((m) => {
                const o = outcomeText(m);
                return (
                  <button
                    key={m.id}
                    onClick={() => onWatch(m.id)}
                    className="match-row w-full text-left mb-2"
                    style={{
                      background: "var(--color-panel2)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 10,
                      padding: "0.6rem 0.8rem",
                      cursor: "pointer",
                    }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold truncate">{o.text}</span>
                      <span className="badge">watch ▸</span>
                    </div>
                  </button>
                );
              })}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
