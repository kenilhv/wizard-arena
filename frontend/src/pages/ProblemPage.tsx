import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getProblem, getLeaderboard, runTournament } from "../api";
import { fetchContests } from "../lib/contests";
import ReviewPanel from "../components/ReviewPanel";
import type { ProblemDetail, Leaderboard as LB, Contest } from "../types";
import { useUser } from "../context/UserContext";
import Leaderboard from "../components/Leaderboard";
import SubmitPanel from "../components/SubmitPanel";
import ReplayModal from "../components/ReplayModal";
import ContestBar from "../components/ContestBar";
import { IconTrophy, IconUpload, IconBolt, IconArrowLeft, IconShield } from "../components/icons";

type Tab = "leaderboard" | "submit" | "review";

export default function ProblemPage() {
  const { slug = "" } = useParams();
  const { user } = useUser();
  const [params, setParams] = useSearchParams();
  const contestId = params.get("contest");

  const [detail, setDetail] = useState<ProblemDetail | null>(null);
  const [lb, setLb] = useState<LB | null>(null);
  const [contests, setContests] = useState<Contest[]>([]);
  const [tab, setTab] = useState<Tab>("leaderboard");
  const [replayId, setReplayId] = useState<string | null>(null);
  const isHostOrAdmin = user && (user.role === "host" || user.role === "admin");

  const [running, setRunning] = useState(false);

  const setContestId = (id: string | null) => {
    const next = new URLSearchParams(params);
    if (id) next.set("contest", id);
    else next.delete("contest");
    setParams(next, { replace: true });
  };

  const refresh = useCallback(async (cid: string | null) => {
    setLb(await getLeaderboard(slug, cid));
  }, [slug]);

  useEffect(() => {
    fetchContests().then(setContests).catch(() => {});
  }, []);

  useEffect(() => {
    if (!slug) return;
    setDetail(null);
    setLb(null);
    getProblem(slug).then(setDetail).catch(() => {});
    refresh(contestId).catch(() => {});
  }, [slug, contestId, refresh]);

  async function onRunTournament() {
    setRunning(true);
    try {
      await runTournament(slug, contestId);
      await refresh(contestId);
    } finally {
      setRunning(false);
    }
  }

  if (!detail) {
    return (
      <div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]">
        <IconArrowLeft size={15} /> All Problems
      </Link>
        <div className="text-[var(--color-muted)] mt-4">Loading problem…</div>
      </div>
    );
  }

  return (
    <div>
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-muted)] hover:text-[var(--color-text)]">
        <IconArrowLeft size={15} /> All Problems
      </Link>

      <div className="grid gap-6 lg:grid-cols-[330px_minmax(0,1fr)] mt-3">
        {/* Left: problem brief */}
        <aside className="space-y-4 min-w-0">
          <div className="panel p-5">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-2xl font-extrabold glow-text">{detail.title}</h2>
              {detail.sponsor && <span className="badge gold-text">{detail.sponsor}</span>}
            </div>
            <p className="text-[var(--color-muted)]">{detail.tagline}</p>
          </div>

          {detail.rules?.length > 0 && (
            <div className="panel p-5">
              <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--color-muted)] mb-2">Rules</h3>
              <ul className="space-y-1 text-sm">
                {detail.rules.map((r, i) => (
                  <li key={i} className="flex gap-2"><span className="gold-text">▸</span><span>{r}</span></li>
                ))}
              </ul>
            </div>
          )}

          <div className="panel p-5">
            <h3 className="text-sm font-bold uppercase tracking-wide text-[var(--color-muted)] mb-2">
              Harness template
            </h3>
            <textarea
              readOnly
              className="w-full font-mono text-xs"
              style={{
                background: "var(--color-bg)", border: "1px solid var(--color-border)",
                borderRadius: 8, padding: "0.75rem", minHeight: 220, color: "var(--color-text)",
              }}
              value={detail.template}
            />
          </div>
        </aside>

        {/* Right: workspace */}
        <section className="@container min-w-0">
          <ContestBar
            contests={contests}
            selected={contestId}
            onSelect={setContestId}
            problemSlug={slug}
          />

          <div className="flex items-center gap-2 mt-4 mb-4">
            <button className={`tab inline-flex items-center gap-1.5 ${tab === "leaderboard" ? "active" : ""}`} onClick={() => setTab("leaderboard")}>
              <IconTrophy size={15} /> Leaderboard
            </button>
            <button className={`tab inline-flex items-center gap-1.5 ${tab === "submit" ? "active" : ""}`} onClick={() => setTab("submit")}>
              <IconUpload size={15} /> Submit Harness
            </button>
            {isHostOrAdmin && (
              <button className={`tab inline-flex items-center gap-1.5 ${tab === "review" ? "active" : ""}`} onClick={() => setTab("review")}>
                <IconShield size={15} /> Review
              </button>
            )}
            {tab === "leaderboard" && (
              <button className="btn btn-primary ml-auto inline-flex items-center gap-1.5" disabled={running} onClick={onRunTournament}>
                <IconBolt size={15} />
                {running ? "Running…" : detail.kind === "h2h" ? "Run Tournament" : "Run Evaluation"}
              </button>
            )}
          </div>

          {tab === "leaderboard" && lb && (
            <Leaderboard data={lb} onWatch={setReplayId} sponsor={detail.sponsor} />
          )}
          {tab === "leaderboard" && !lb && (
            <div className="text-[var(--color-muted)]">Loading the arena…</div>
          )}
          {tab === "submit" && (
            <SubmitPanel
              problem={detail}
              contestId={contestId}
              user={user}
              onEntered={() => { refresh(contestId); setTab("leaderboard"); }}
            />
          )}
          {tab === "review" && isHostOrAdmin && (
            <ReviewPanel problemSlug={slug} />
          )}
        </section>
      </div>

      {replayId && <ReplayModal id={replayId} onClose={() => setReplayId(null)} />}
    </div>
  );
}
