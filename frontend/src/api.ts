import type {
  Contest, Leaderboard, MatchDetail, ProblemDetail, ProblemMeta, NoCodeConfig, HostSubmission,
} from "./types";
import { getToken } from "./auth";

const BASE = import.meta.env.VITE_API_BASE ?? "";

function headers(json = false): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["Content-Type"] = "application/json";
  const token = getToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { headers: headers() });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json() as Promise<T>;
}

export const getProblems = (contestId?: string | null) =>
  get<{ problems: ProblemMeta[] }>(`/api/problems${contestId ? `?contest_id=${contestId}` : ""}`);

export const getProblem = (slug: string) => get<ProblemDetail>(`/api/problem/${slug}`);

export const getLeaderboard = (slug: string, contestId?: string | null) =>
  get<Leaderboard>(`/api/leaderboard/${slug}${contestId ? `?contest_id=${contestId}` : ""}`);

export const getMatch = (id: string) => get<MatchDetail>(`/api/match/${id}`);

export const getContests = (problemSlug?: string) =>
  get<{ contests: Contest[] }>(`/api/contests${problemSlug ? `?problem_slug=${problemSlug}` : ""}`);

export const getHostSubmissions = (problemSlug?: string, contestId?: string | null) => {
  const params = new URLSearchParams();
  if (problemSlug) params.set("problem_slug", problemSlug);
  if (contestId) params.set("contest_id", contestId);
  const q = params.toString();
  return get<{ submissions: HostSubmission[] }>(`/api/host/submissions${q ? `?${q}` : ""}`);
};

export async function postHostReport(submissionId: string, reason: string) {
  const r = await fetch(`${BASE}/api/host/report`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ submission_id: submissionId, reason }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `report -> ${r.status}`);
  }
  return r.json() as Promise<{ id: string; ok: boolean }>;
}

export async function runTournament(slug: string, contestId?: string | null) {
  const q = contestId ? `?contest_id=${contestId}` : "";
  const r = await fetch(`${BASE}/api/tournament/run/${slug}${q}`, {
    method: "POST",
    headers: headers(),
  });
  if (!r.ok) throw new Error(`tournament -> ${r.status}`);
  return r.json();
}

export async function submitCode(
  slug: string, name: string, author: string, code: string, contestId?: string | null,
) {
  const fd = new FormData();
  fd.append("problem_slug", slug);
  fd.append("mode", "code");
  fd.append("name", name);
  fd.append("author", author);
  fd.append("code", code);
  if (contestId) fd.append("contest_id", contestId);
  const r = await fetch(`${BASE}/api/submit`, { method: "POST", headers: headers(), body: fd });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `submit -> ${r.status}`);
  }
  return r.json() as Promise<{ id: string; valid: boolean; error: string }>;
}

export async function submitNoCode(
  slug: string, name: string, author: string, cfg: NoCodeConfig, contestId?: string | null,
) {
  const fd = new FormData();
  fd.append("problem_slug", slug);
  fd.append("mode", "nocode");
  fd.append("name", name);
  fd.append("author", author);
  fd.append("model", cfg.model);
  fd.append("system_prompt", cfg.system_prompt);
  fd.append("temperature", String(cfg.temperature));
  fd.append("auto_guard", String(cfg.auto_guard));
  if (contestId) fd.append("contest_id", contestId);
  const r = await fetch(`${BASE}/api/submit`, { method: "POST", headers: headers(), body: fd });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `submit -> ${r.status}`);
  }
  return r.json() as Promise<{ id: string; valid: boolean; error: string }>;
}
