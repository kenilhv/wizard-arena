import { Link, Outlet, useLocation } from "react-router-dom";
import AuthPanel from "./AuthPanel";
import Logo from "./Logo";
import { IconShield, IconGauge } from "./icons";
import { useUser } from "../context/UserContext";

export default function Layout() {
  const { user, setUser, logout, authError } = useUser();
  const loc = useLocation();
  const isHostOrAdmin = user && (user.role === "host" || user.role === "admin");

  return (
    <div className="min-h-full">
      <header className="max-w-6xl mx-auto px-5 pt-7 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="block">
            <Logo size={44} />
          </Link>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              {isHostOrAdmin && (
                <Link
                  to="/admin"
                  className={`tab inline-flex items-center gap-1.5 ${loc.pathname === "/admin" ? "active" : ""}`}
                >
                  {user.role === "admin" ? <IconShield size={15} /> : <IconGauge size={15} />}
                  {user.role === "admin" ? "Admin" : "Host"}
                </Link>
              )}
              <AuthPanel
                user={user}
                onAuth={(u) => setUser(u)}
                onLogout={logout}
              />
            </div>
            <div className="text-right text-xs text-[var(--color-muted)]">
              <div>data <span className="font-mono">InsForge</span> · inference <span className="font-mono">Nebius</span></div>
              <div>search <span className="font-mono">You.com</span> · judge <span className="font-mono">Replit</span></div>
            </div>
          </div>
        </div>
        {authError && (
          <p className="mt-2 text-sm" style={{ color: "#fb7185" }}>
            Sign-in error: {authError}
          </p>
        )}
      </header>

      <main className="max-w-6xl mx-auto px-5 pb-16">
        <Outlet />
      </main>
    </div>
  );
}
