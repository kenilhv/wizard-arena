import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProblems } from "../api";
import { fetchContests } from "../lib/contests";
import { problemIcon, Dot } from "../components/icons";
import type { ProblemMeta, Contest } from "../types";

const SPONSOR_CHIP: Record<string, string> = {
  nebius: "sp-nebius",
  "you.com": "sp-youcom",
  youcom: "sp-youcom",
  tavily: "sp-tavily",
  replit: "sp-replit",
  insforge: "sp-insforge",
};

function chipClass(sponsor: string) {
  return SPONSOR_CHIP[sponsor.toLowerCase()] || "";
}

const kindLabel = (kind: string) => (kind === "h2h" ? "Head-to-Head" : "Task");

function fmt(ts: number) {
  return new Date(ts * 1000).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

export default function LobbyPage() {
  const [problems, setProblems] = useState<ProblemMeta[]>([]);
  const [contests, setContests] = useState<Contest[]>([]);

  useEffect(() => {
    getProblems().then((d) => setProblems(d.problems)).catch(() => {});
    fetchContests().then(setContests).catch(() => {});
  }, []);

  const liveContests = contests.filter((c) => c.is_open || c.is_upcoming);

  return (
    <div className="space-y-9">
      {/* Hero */}
      <section className="fade-up pt-2">
        <h2 className="text-3xl md:text-5xl font-extrabold hero-title leading-tight">
          Don't play the game.<br />Engineer the agent that plays it.
        </h2>
        <p className="text-[var(--color-muted)] mt-3 max-w-2xl text-base md:text-lg">
          Competitive harness engineering. Pick a problem, build your agent — in code or
          no-code — and climb a live leaderboard ranked on wins <em>and</em> token efficiency.
        </p>

        <div className="flex flex-wrap gap-3 mt-5">
          <div className="stat"><b>{problems.length || "—"}</b><span>Problems</span></div>
          <div className="stat"><b>{liveContests.length}</b><span>Live / upcoming</span></div>
        </div>
      </section>

      {/* Contests banner */}
      {liveContests.length > 0 && (
        <section className="fade-up">
          <div className="text-xs font-bold uppercase tracking-wide text-[var(--color-muted)] mb-2">
            Contests
          </div>
          <div className="flex flex-wrap gap-2">
            {liveContests.map((c) => (
              <Link
                key={c.id}
                to={`/problem/${c.problem_slug}?contest=${c.id}`}
                className="panel px-3 py-2 text-sm flex items-center gap-2 hover:border-[var(--color-arcane-bright)]"
                style={{ borderRadius: 12 }}
                title={`${fmt(c.start_at)} – ${fmt(c.end_at)}`}
              >
                <span className="inline-flex items-center gap-1.5"
                  style={{ color: c.is_open ? "#fb7185" : "var(--color-cyan)" }}>
                  <Dot color={c.is_open ? "#fb7185" : "#22d3ee"} />
                  {c.is_open ? "LIVE" : "Upcoming"}
                </span>
                <b>{c.title}</b>
                <span className="text-[var(--color-muted)]">→</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Problem cards */}
      <section className="fade-up">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {problems.map((p) => {
            const sp = chipClass(p.sponsor);
            return (
              <Link key={p.slug} to={`/problem/${p.slug}`} className={`card ${sp} p-5 flex flex-col gap-3`}>
                <div className="flex items-start justify-between gap-2">
                  <span className="grid place-items-center rounded-xl"
                    style={{ width: 44, height: 44, background: "var(--color-panel2)",
                      border: "1px solid var(--color-border)", color: "var(--color-arcane-bright)" }}>
                    {problemIcon(p.slug, p.kind, 22)}
                  </span>
                  {p.sponsor && <span className={`chip ${sp}`}>{p.sponsor}</span>}
                </div>
                <div>
                  <h3 className="text-lg font-extrabold">{p.title}</h3>
                  <p className="text-sm text-[var(--color-muted)] mt-1 leading-snug">{p.tagline}</p>
                </div>
                <div className="flex items-center gap-2 mt-auto pt-2">
                  <span className="badge">{kindLabel(p.kind)}</span>
                  {p.supports_nocode && <span className="badge">no-code ✓</span>}
                </div>
                <span className="card-cta btn text-center mt-1">Compete →</span>
              </Link>
            );
          })}
          {problems.length === 0 && (
            <div className="text-[var(--color-muted)]">Loading the arena…</div>
          )}
        </div>
      </section>
    </div>
  );
}
