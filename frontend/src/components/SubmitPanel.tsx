import { useEffect, useState } from "react";
import { submitCode, submitNoCode, runTournament } from "../api";
import type { ProblemDetail, User } from "../types";

const CONTRACT: Record<string, string> = {
  connect4: "class Harness with move(self, view, llm) -> int",
  "research-agent": "class Harness with research(self, question, search, llm) -> str",
  "coding-bench": "class Harness with solve(self, spec, llm) -> str",
};

export default function SubmitPanel({
  problem, contestId, user, onEntered,
}: {
  problem: ProblemDetail;
  contestId: string | null;
  user: User | null;
  onEntered: () => void;
}) {
  const [mode, setMode] = useState<"code" | "nocode">("nocode");
  const [name, setName] = useState("MyHarness");
  const [code, setCode] = useState(problem.template);

  const [model, setModel] = useState(problem.models[0]?.id ?? "mock");
  const [systemPrompt, setSystemPrompt] = useState(
    problem.slug === "research-agent"
      ? "Search first, then synthesize. Be concise and factual."
      : problem.slug === "coding-bench"
        ? "Write minimal, correct Python. No comments or markdown."
        : "Control the center. Build your own threats while blocking the opponent."
  );
  const [temperature, setTemperature] = useState(0.2);
  const [autoGuard, setAutoGuard] = useState(problem.slug === "connect4");

  const [busy, setBusy] = useState<"" | "submitting" | "battling">("");
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    setCode(problem.template);
  }, [problem.slug, problem.template]);

  if (!user) {
    return (
      <div className="panel p-8 text-center">
        <p className="text-lg font-bold glow-text mb-2">Sign in to submit</p>
        <p className="text-[var(--color-muted)]">
          Submissions are private — only you (and hosts) can see your harness code.
        </p>
      </div>
    );
  }

  async function enterArena() {
    if (!user) return;
    setResult(null);
    setBusy("submitting");
    try {
      const r = mode === "code"
        ? await submitCode(problem.slug, name || "MyHarness", user.display_name, code, contestId)
        : await submitNoCode(problem.slug, name || "MyHarness", user.display_name,
            { model, system_prompt: systemPrompt, temperature, auto_guard: autoGuard }, contestId);
      if (!r.valid) {
        setResult({ ok: false, msg: r.error || "harness rejected" });
        setBusy("");
        return;
      }
      setBusy("battling");
      await runTournament(problem.slug, contestId);
      setResult({ ok: true, msg: `${name} entered the arena!` });
      onEntered();
    } catch (e) {
      setResult({ ok: false, msg: String(e) });
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="grid lg:grid-cols-[1fr_320px] gap-5">
      <div className="panel p-4">
        <div className="flex items-center gap-2 mb-3">
          {problem.supports_nocode && (
            <button className={`tab ${mode === "nocode" ? "active" : ""}`} onClick={() => setMode("nocode")}>
              🧩 No-code
            </button>
          )}
          <button className={`tab ${mode === "code" ? "active" : ""}`} onClick={() => setMode("code")}>
            💻 Code
          </button>
          {contestId && <span className="badge ml-auto" style={{ color: "#fb7185" }}>contest submission</span>}
        </div>

        <div className="flex flex-wrap items-center gap-3 mb-3">
          <input className="btn" style={{ background: "var(--color-bg)", flex: "1 1 140px" }}
            value={name} onChange={(e) => setName(e.target.value)} placeholder="Harness name" />
        </div>

        {mode === "nocode" ? (
          <div className="space-y-3">
            <label className="block">
              <span className="text-xs text-[var(--color-muted)] font-bold uppercase tracking-wide">Model (Nebius)</span>
              <select className="btn w-full mt-1" style={{ background: "var(--color-bg)" }}
                value={model} onChange={(e) => setModel(e.target.value)}>
                {problem.models.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="text-xs text-[var(--color-muted)] font-bold uppercase tracking-wide">System prompt / strategy</span>
              <textarea className="scroll" spellCheck={false} value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                style={{ width: "100%", height: 160, marginTop: 4, background: "#0b0717",
                  color: "#d6cdf0", border: "1px solid var(--color-border)", borderRadius: 10,
                  padding: "10px 12px", fontFamily: "inherit", fontSize: 14, lineHeight: 1.5,
                  resize: "vertical", outline: "none" }} />
            </label>
            <div className="flex flex-wrap items-center gap-4">
              <label className="text-sm">
                <span className="text-[var(--color-muted)]">Temp </span>
                <input type="number" min={0} max={1} step={0.1} value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="btn" style={{ width: 80, background: "var(--color-bg)", padding: "0.3rem 0.5rem" }} />
              </label>
              {problem.slug === "connect4" && (
                <label className="text-sm flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={autoGuard} onChange={(e) => setAutoGuard(e.target.checked)} />
                  <span>Auto-guard forced moves</span>
                </label>
              )}
            </div>
          </div>
        ) : (
          <>
            <textarea className="scroll" spellCheck={false} value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  e.preventDefault();
                  const t = e.currentTarget; const s = t.selectionStart;
                  setCode(code.slice(0, s) + "    " + code.slice(t.selectionEnd));
                  requestAnimationFrame(() => { t.selectionStart = t.selectionEnd = s + 4; });
                }
              }}
              style={{ width: "100%", height: 440, resize: "vertical", background: "#0b0717",
                color: "#d6cdf0", border: "1px solid var(--color-border)", borderRadius: 10,
                padding: "12px 14px", fontFamily: "JetBrains Mono, Consolas, ui-monospace, monospace",
                fontSize: 13, lineHeight: 1.5, outline: "none" }} />
            <p className="text-xs text-[var(--color-muted)] mt-1">
              Python · {CONTRACT[problem.slug] || "class Harness"}
            </p>
          </>
        )}

        <div className="flex items-center gap-3 mt-3">
          <button className="btn btn-gold" disabled={!!busy} onClick={enterArena}>
            {busy === "submitting" ? "Validating…" : busy === "battling" ? "Running evaluation…" : "Submit & Run"}
          </button>
          {result && (
            <span style={{ color: result.ok ? "var(--color-cyan)" : "#fb7185", fontWeight: 700 }}>
              {result.ok ? "✓ " : "✗ "}{result.msg}
            </span>
          )}
        </div>
      </div>

      <div className="panel p-5">
        <h3 className="font-extrabold glow-text mb-2">📜 {problem.title}</h3>
        <p className="text-sm text-[var(--color-muted)] mb-3">{problem.tagline}</p>
        <ul className="text-sm space-y-2">
          {problem.rules.map((r, i) => (
            <li key={i} className="flex gap-2"><span className="gold-text">▸</span><span>{r}</span></li>
          ))}
        </ul>
        {problem.llm_mock && (
          <div className="mt-4 badge" style={{ color: "var(--color-amber)" }}>
            mock LLM — set NEBIUS_API_KEY
          </div>
        )}
        {problem.search_mock && problem.slug === "research-agent" && (
          <div className="mt-2 badge" style={{ color: "var(--color-cyan)" }}>
            mock search — set YOU_API_KEY
          </div>
        )}
        <p className="text-xs text-[var(--color-muted)] mt-4">
          🔒 Your submission code is private. Leaderboards show scores only.
        </p>
      </div>
    </div>
  );
}
