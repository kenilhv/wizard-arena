-- Arena platform schema for InsForge (Postgres)
-- Run via InsForge CLI: npx @insforge/cli db migrations up

CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'host', 'admin')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contests (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  problem_slug TEXT NOT NULL,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status TEXT DEFAULT 'scheduled',
  host_id UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  problem_slug TEXT NOT NULL,
  contest_id TEXT REFERENCES contests(id),
  user_id UUID NOT NULL REFERENCES profiles(id),
  name TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('code', 'nocode')),
  code TEXT,
  nocode JSONB,
  status TEXT NOT NULL,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tournaments (
  id TEXT PRIMARY KEY,
  problem_slug TEXT NOT NULL,
  contest_id TEXT REFERENCES contests(id),
  kind TEXT NOT NULL,
  standings JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  submission_id TEXT NOT NULL REFERENCES submissions(id),
  reporter_id UUID NOT NULL REFERENCES profiles(id),
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: users never read others' submission code
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY submissions_select_own ON submissions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY submissions_select_host ON submissions
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles p WHERE p.id = auth.uid() AND p.role IN ('host', 'admin'))
  );

CREATE POLICY submissions_insert_own ON submissions
  FOR INSERT WITH CHECK (auth.uid() = user_id);
