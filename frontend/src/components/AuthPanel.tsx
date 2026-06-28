import { useState } from "react";
import { insforge, completeArenaSession } from "../lib/insforge";
import { clearSession } from "../auth";
import { IconShield, IconGauge, IconUser } from "./icons";
import type { User } from "../types";

export default function AuthPanel({
  user, onAuth, onLogout,
}: {
  user: User | null;
  onAuth: (u: User) => void;
  onLogout: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [verifyCode, setVerifyCode] = useState("");
  const [needsVerify, setNeedsVerify] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setErr("");
    setBusy(true);
    try {
      if (needsVerify) {
        const { data, error } = await insforge.auth.verifyEmail({ email, otp: verifyCode });
        if (error || !data?.accessToken || !data.user) throw new Error(error?.message || "verification failed");
        const arenaUser = await completeArenaSession(data.accessToken, data.user, name || undefined);
        onAuth(arenaUser);
        setOpen(false);
        setNeedsVerify(false);
        return;
      }
      if (mode === "login") {
        const { data, error } = await insforge.auth.signInWithPassword({ email, password });
        if (error || !data?.accessToken) throw new Error(error?.message || "sign in failed");
        const arenaUser = await completeArenaSession(data.accessToken, data.user);
        onAuth(arenaUser);
        setOpen(false);
      } else {
        const displayName = name || email.split("@")[0];
        const { data, error } = await insforge.auth.signUp({
          email, password, name: displayName,
        });
        if (error) throw new Error(error.message);
        if (data?.requireEmailVerification) {
          setNeedsVerify(true);
          return;
        }
        if (data?.accessToken && data.user) {
          const arenaUser = await completeArenaSession(data.accessToken, data.user, displayName);
          onAuth(arenaUser);
          setOpen(false);
        }
      }
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function oauth(provider: "google" | "github") {
    setErr("");
    setBusy(true);
    try {
      const { error } = await insforge.auth.signInWithOAuth(provider, {
        redirectTo: window.location.origin + "/",
      });
      if (error) setErr(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await insforge.auth.signOut();
    clearSession();
    onLogout();
  }

  if (user) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className="badge inline-flex items-center gap-1.5" style={{ color: "var(--color-cyan)" }}>
          {user.role === "admin" ? <IconShield size={13} /> : user.role === "host" ? <IconGauge size={13} /> : <IconUser size={13} />}
          {user.display_name} · <span className="gold-text">{user.role}</span>
        </span>
        <button className="btn" style={{ padding: "0.35rem 0.7rem", fontSize: 12 }} onClick={signOut}>
          Sign out
        </button>
      </div>
    );
  }

  return (
    <>
      <button className="btn btn-primary" style={{ padding: "0.45rem 0.9rem", fontSize: 13 }}
        onClick={() => setOpen(true)}>
        Sign in to compete
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.65)" }} onClick={() => setOpen(false)}>
          <div className="panel p-5 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-extrabold glow-text mb-3">Enter the Arena</h2>
            {!needsVerify && (
              <div className="flex gap-2 mb-3">
                <button className={`tab ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>Sign in</button>
                <button className={`tab ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>Register</button>
              </div>
            )}
            {needsVerify ? (
              <>
                <p className="text-sm text-[var(--color-muted)] mb-2">Enter the 6-digit code sent to {email}</p>
                <input className="btn w-full mb-3" style={{ background: "var(--color-bg)" }}
                  placeholder="123456" value={verifyCode} onChange={(e) => setVerifyCode(e.target.value)} />
              </>
            ) : (
              <>
                {mode === "register" && (
                  <input className="btn w-full mb-2" style={{ background: "var(--color-bg)" }}
                    placeholder="Display name" value={name} onChange={(e) => setName(e.target.value)} />
                )}
                <input className="btn w-full mb-2" style={{ background: "var(--color-bg)" }}
                  placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
                <input className="btn w-full mb-3" type="password" style={{ background: "var(--color-bg)" }}
                  placeholder="Password (min 6 chars)" value={password} onChange={(e) => setPassword(e.target.value)} />
                <div className="flex gap-2 mb-3">
                  <button className="btn flex-1" type="button" onClick={() => oauth("google")}>Google</button>
                  <button className="btn flex-1" type="button" onClick={() => oauth("github")}>GitHub</button>
                </div>
              </>
            )}
            <p className="text-xs text-[var(--color-muted)] mb-3">
              Email + password · instant sign-in · submissions are private
            </p>
            {err && <p className="text-sm mb-2" style={{ color: "#fb7185" }}>{err}</p>}
            <div className="flex gap-2">
              <button className="btn btn-gold flex-1" disabled={busy} onClick={submit}>
                {busy ? "…" : needsVerify ? "Verify" : mode === "login" ? "Sign in" : "Create account"}
              </button>
              <button className="btn" onClick={() => setOpen(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
