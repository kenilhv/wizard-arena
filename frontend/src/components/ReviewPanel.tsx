import { useEffect, useState } from "react";
import { getHostSubmissions, postHostReport } from "../api";
import type { HostSubmission } from "../types";

export default function ReviewPanel({ problemSlug }: { problemSlug: string }) {
  const [subs, setSubs] = useState<HostSubmission[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    const res = await getHostSubmissions(problemSlug);
    setSubs(res.submissions);
  }

  useEffect(() => {
    load().catch(() => setSubs([]));
  }, [problemSlug]);

  async function report(sub: HostSubmission) {
    const reason = reasons[sub.id]?.trim() || "Flagged during host review";
    setBusy(sub.id);
    setMsg("");
    try {
      await postHostReport(sub.id, reason);
      setMsg(`Report saved for ${sub.name}`);
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(null);
    }
  }

  if (subs.length === 0) {
    return <p className="text-sm text-[var(--color-muted)]">No submissions for this problem yet.</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-[var(--color-muted)]">
        Hosts and admins can review all submissions. Normal users only see their own code (InsForge RLS).
      </p>
      {subs.map((s) => {
        const open = expanded === s.id;
        const codePreview = s.mode === "code"
          ? (s.code || "(no code)")
          : JSON.stringify(s.nocode ?? {}, null, 2);
        return (
          <div key={s.id} className="panel p-4 space-y-2">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div className="font-bold">{s.name}</div>
                <div className="text-xs text-[var(--color-muted)] mt-0.5">
                  {s.author} · {s.mode} · <span className="badge">{s.status}</span>
                </div>
                <div className="text-xs text-[var(--color-muted)] font-mono mt-0.5">{s.id}</div>
              </div>
              <button className="btn" style={{ padding: "0.25rem 0.6rem", fontSize: 12 }}
                onClick={() => setExpanded(open ? null : s.id)}>
                {open ? "Hide code" : "Show code"}
              </button>
            </div>
            {open && (
              <textarea readOnly className="w-full font-mono text-xs"
                style={{
                  background: "var(--color-bg)", border: "1px solid var(--color-border)",
                  borderRadius: 8, padding: "0.75rem", minHeight: 160, color: "var(--color-text)",
                }}
                value={codePreview}
              />
            )}
            {s.error && (
              <p className="text-xs" style={{ color: "#fb7185" }}>{s.error}</p>
            )}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <input
                className="flex-1 min-w-[180px] text-sm"
                placeholder="Report reason (optional)"
                value={reasons[s.id] || ""}
                onChange={(e) => setReasons({ ...reasons, [s.id]: e.target.value })}
              />
              <button className="btn btn-gold" style={{ padding: "0.35rem 0.75rem", fontSize: 12 }}
                disabled={busy === s.id}
                onClick={() => report(s)}>
                {busy === s.id ? "Saving…" : "Report"}
              </button>
            </div>
          </div>
        );
      })}
      {msg && <p className="text-sm" style={{ color: "var(--color-cyan)" }}>{msg}</p>}
    </div>
  );
}
