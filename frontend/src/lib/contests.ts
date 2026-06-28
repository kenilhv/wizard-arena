import { insforge } from "./insforge";
import type { Contest } from "../types";

type ContestRow = {
  id: string;
  title: string;
  problem_slug: string;
  start_at: string | number;
  end_at: string | number;
  status?: string;
};

function toUnix(ts: string | number): number {
  if (typeof ts === "number") return ts;
  return Math.floor(new Date(ts).getTime() / 1000);
}

export async function fetchContests(problemSlug?: string): Promise<Contest[]> {
  let q = insforge.database
    .from("contests")
    .select("id, title, problem_slug, start_at, end_at, status")
    .order("start_at", { ascending: true });
  if (problemSlug) q = q.eq("problem_slug", problemSlug);
  const { data, error } = await q;
  if (error || !data) return [];
  const now = Date.now() / 1000;
  return (data as ContestRow[]).map((c) => {
    const start_at = toUnix(c.start_at);
    const end_at = toUnix(c.end_at);
    return {
      id: c.id,
      title: c.title,
      problem_slug: c.problem_slug,
      start_at,
      end_at,
      status: c.status || "scheduled",
      is_open: start_at <= now && now <= end_at,
      is_upcoming: start_at > now,
      is_closed: end_at < now,
    };
  });
}
