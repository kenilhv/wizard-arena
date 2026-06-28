import { createClient } from "@insforge/sdk";
import { saveSession } from "../auth";
import type { User } from "../types";

// Anon key + URL are public (shipped to the browser), so safe as build fallbacks
// — this keeps the production build working even if the env vars aren't set.
export const insforge = createClient({
  baseUrl: import.meta.env.VITE_INSFORGE_URL || "https://wphij32t.us-west.insforge.app",
  anonKey: import.meta.env.VITE_INSFORGE_ANON_KEY || "ik_d2022fcc8444eea47f1a8cfc2a78dad1",
});

function displayNameFor(
  raw: { email: string; profile?: { name?: string } | null },
  fallback?: string,
) {
  return fallback || raw.profile?.name || raw.email.split("@")[0];
}

export async function fetchArenaProfile(userId: string): Promise<Pick<User, "role" | "display_name"> | null> {
  const { data, error } = await insforge.database
    .from("profiles")
    .select("display_name, role")
    .eq("id", userId)
    .maybeSingle();
  if (error || !data) return null;
  return { display_name: data.display_name, role: data.role as User["role"] };
}

/** Ensure every auth user has an Arena profile row (role defaults to 'user'). */
export async function ensureProfile(userId: string, displayName: string) {
  const { data } = await insforge.database
    .from("profiles")
    .select("id")
    .eq("id", userId)
    .maybeSingle();
  if (data) return;
  const { error } = await insforge.database.from("profiles").insert([{
    id: userId,
    display_name: displayName,
    role: "user",
  }]);
  if (error) throw new Error(`failed to create profile: ${error.message}`);
}

export function mapInsforgeUser(
  raw: { id: string; email: string; profile?: { name?: string } | null },
  profile: Pick<User, "role" | "display_name"> | null,
): User {
  return {
    id: raw.id,
    email: raw.email,
    display_name: profile?.display_name || raw.profile?.name || raw.email.split("@")[0],
    role: profile?.role || "user",
  };
}

/** Create profile if missing, persist session, return Arena user. */
export async function completeArenaSession(
  accessToken: string,
  rawUser: { id: string; email: string; profile?: { name?: string } | null },
  displayName?: string,
): Promise<User> {
  await ensureProfile(rawUser.id, displayNameFor(rawUser, displayName));
  const profile = await fetchArenaProfile(rawUser.id);
  const arenaUser = mapInsforgeUser(rawUser, profile);
  saveSession(accessToken, arenaUser);
  return arenaUser;
}

/** Wait for OAuth callback exchange, then hydrate Arena session + UI user. */
export async function restoreArenaSession(): Promise<{ user: User | null; error?: string }> {
  const params = new URLSearchParams(window.location.search);
  const oauthErr = params.get("error") || params.get("insforge_error");
  if (oauthErr) {
    return { user: null, error: oauthErr };
  }

  const { data, error } = await insforge.auth.getCurrentUser();
  if (error) return { user: null, error: error.message };

  let user = data?.user ?? null;
  let accessToken: string | null = null;

  const refreshed = await insforge.auth.refreshSession();
  if (refreshed.data?.accessToken && refreshed.data.user) {
    user = refreshed.data.user;
    accessToken = refreshed.data.accessToken;
  }

  if (!user) return { user: null };

  if (!accessToken) {
    const again = await insforge.auth.getCurrentUser();
    user = again.data?.user ?? user;
    const retry = await insforge.auth.refreshSession();
    accessToken = retry.data?.accessToken ?? null;
  }

  await ensureProfile(user.id, displayNameFor(user));
  const profile = await fetchArenaProfile(user.id);
  const arenaUser = mapInsforgeUser(user, profile);
  if (accessToken) saveSession(accessToken, arenaUser);
  return { user: arenaUser };
}

export function consumeOAuthCallbackParams(): string | null {
  const params = new URLSearchParams(window.location.search);
  const err = params.get("error") || params.get("insforge_error");
  const hadOAuth = params.has("insforge_code") || params.has("error") || params.has("insforge_error");
  if (hadOAuth) {
    const clean = new URL(window.location.href);
    ["insforge_code", "error", "insforge_error", "insforge_status", "insforge_type"].forEach((k) => {
      clean.searchParams.delete(k);
    });
    window.history.replaceState({}, "", clean.pathname + clean.search + clean.hash);
  }
  return err;
}
