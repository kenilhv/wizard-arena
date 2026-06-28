export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "host" | "admin";
}

export interface Usage {
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface Standing {
  rank: number;
  id: string;
  name: string;
  author: string;
  mode: "code" | "nocode";
  points: number;
  wins: number;
  draws: number;
  losses: number;
  games: number;
  tokens: number;
  cost_usd: number;
  forfeits: number;
  // task problems
  score?: number;
  correct?: number;
  total?: number;
  accuracy?: number;
  search_queries?: number;
  latency_ms?: number;
}

export interface MatchSummary {
  id: string;
  name_a: string;
  name_b: string;
  entry_a: string;
  entry_b: string;
  winner: "A" | "B" | "draw";
  reason: string;
}

export interface TaskRunSummary {
  id: string;
  entry_id: string;
  entry_name: string;
  task_id: string;
  task_label: string;
  correct: number;
  detail: string;
}

export interface Frame {
  board: number[][];
  move: number | null;
  mover: "A" | "B" | null;
  ply: number;
}

export interface MatchDetail {
  id: string;
  names: { A: string; B: string };
  entry_ids: { A: string; B: string };
  winner: "A" | "B" | "draw";
  reason: string;
  moves: number[];
  frames: Frame[];
  usage: { A: Usage; B: Usage };
}

export interface Leaderboard {
  tournament_id: string | null;
  kind: string | null;
  standings: Standing[];
  matches: MatchSummary[];
  task_runs?: TaskRunSummary[];
  contest_id?: string | null;
}

export interface ProblemMeta {
  slug: string;
  title: string;
  kind: string;
  sponsor: string;
  tagline: string;
  rules: string[];
  supports_nocode: boolean;
  entries?: number;
}

export interface ModelOption {
  id: string;
  label: string;
}

export interface ProblemDetail extends ProblemMeta {
  template: string;
  models: ModelOption[];
  llm_mock: boolean;
  search_mock?: boolean;
}

export interface NoCodeConfig {
  model: string;
  system_prompt: string;
  temperature: number;
  auto_guard: boolean;
}

export interface Contest {
  id: string;
  title: string;
  problem_slug: string;
  start_at: number;
  end_at: number;
  status: string;
  is_open: boolean;
  is_upcoming: boolean;
  is_closed: boolean;
}

export interface HostSubmission {
  id: string;
  problem_slug: string;
  name: string;
  author: string;
  mode: "code" | "nocode";
  status: string;
  user_id?: string;
  contest_id?: string | null;
  created_at?: number;
  error?: string;
  code?: string;
  nocode?: Record<string, unknown> | null;
}
