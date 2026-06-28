import { useEffect, useState } from "react";
import { insforge } from "../lib/insforge";
import type { User } from "../types";

interface ProfileRow {
  id: string;
  display_name: string;
  role: string;
  email?: string;
}

export default function AdminPanel({ user, onRoleChanged }: { user: User; onRoleChanged: () => void }) {
  const [profiles, setProfiles] = useState<ProfileRow[]>([]);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const isAdmin = user.role === "admin";

  async function load() {
    const { data: profs } = await insforge.database
      .from("profiles")
      .select("id, display_name, role, created_at")
      .order("created_at", { ascending: false });
    setProfiles((profs as ProfileRow[]) || []);
  }

  useEffect(() => { load().catch(() => {}); }, [user.id, user.role]);

  async function setRole(uid: string, role: string) {
    if (!isAdmin) return;
    setBusy(true);
    setMsg("");
    try {
      const { error } = await insforge.database.from("profiles").update({ role }).eq("id", uid);
      if (error) throw new Error(error.message);
      setMsg(`Updated role → ${role}`);
      await load();
      onRoleChanged();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="panel p-5">
        <h2 className="text-lg font-extrabold glow-text mb-2">Your Arena Role</h2>
        <p className="text-sm">
          Signed in as <b>{user.display_name}</b> · role:{" "}
          <span className="badge gold-text">{user.role}</span>
        </p>
        <p className="text-xs text-[var(--color-muted)] mt-2 font-mono break-all">user id: {user.id}</p>
        <p className="text-xs text-[var(--color-muted)] mt-2">
          Roles live in InsForge <span className="font-mono">profiles</span> table (not the Auth dashboard).
          Sign out + back in after a role change to refresh. Use the <b>Review</b> tab on any problem page to
          moderate submissions.
        </p>
      </div>

      {isAdmin && (
        <div className="panel p-5">
          <h2 className="text-lg font-extrabold glow-text mb-3">Manage Roles</h2>
          <p className="text-xs text-[var(--color-muted)] mb-3">Admin can promote users to host or admin.</p>
          <div className="scroll" style={{ overflowX: "auto" }}>
            <table className="lb" style={{ minWidth: 480 }}>
              <thead>
                <tr><th>Name</th><th>Role</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {profiles.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="font-bold">{p.display_name}</div>
                      <div className="text-xs text-[var(--color-muted)] font-mono">{p.id.slice(0, 8)}…</div>
                    </td>
                    <td><span className="badge">{p.role}</span></td>
                    <td className="space-x-1">
                      {p.role !== "user" && (
                        <button className="btn" style={{ padding: "0.25rem 0.5rem", fontSize: 11 }}
                          disabled={busy} onClick={() => setRole(p.id, "user")}>user</button>
                      )}
                      {p.role !== "host" && (
                        <button className="btn" style={{ padding: "0.25rem 0.5rem", fontSize: 11 }}
                          disabled={busy} onClick={() => setRole(p.id, "host")}>host</button>
                      )}
                      {p.role !== "admin" && (
                        <button className="btn btn-gold" style={{ padding: "0.25rem 0.5rem", fontSize: 11 }}
                          disabled={busy} onClick={() => setRole(p.id, "admin")}>admin</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {msg && <p className="text-sm mt-3" style={{ color: "var(--color-cyan)" }}>{msg}</p>}
        </div>
      )}
    </div>
  );
}
