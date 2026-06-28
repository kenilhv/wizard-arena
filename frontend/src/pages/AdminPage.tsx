import { Link } from "react-router-dom";
import { useUser } from "../context/UserContext";
import AdminPanel from "../components/AdminPanel";

export default function AdminPage() {
  const { user, refreshRole } = useUser();

  if (!user || (user.role !== "host" && user.role !== "admin")) {
    return (
      <div>
        <Link to="/" className="text-sm text-[var(--color-muted)] hover:underline">← All Problems</Link>
        <div className="panel p-6 mt-4">
          <h2 className="text-lg font-extrabold mb-1">Restricted</h2>
          <p className="text-sm text-[var(--color-muted)]">
            This area is for hosts and admins only.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Link to="/" className="text-sm text-[var(--color-muted)] hover:underline">← All Problems</Link>
      <div className="mt-4">
        {/* Re-fetch profile so a self role change reflects without full reload */}
        <AdminPanel user={user} onRoleChanged={() => { refreshRole().catch(() => {}); }} />
      </div>
    </div>
  );
}
