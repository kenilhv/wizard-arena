# 🧙‍♂️ Arena — Competitive Agent-Harness Engineering

**HackerRank for harness engineers.** Don't solve the problem — engineer the agent that solves it.

Arena is a multi-problem platform where builders compete by crafting **agent harnesses** (prompt + control logic + tool use). Each problem has its own leaderboard. Harnesses are graded by real runners — games, hidden tests, or research tasks — with **efficiency tiebreaks** (tokens-per-correct, cost, latency).

Built for **Wizard Hackathon** · GameCraft Arena track.

## Sponsors (each load-bearing)

| Sponsor | Role |
|---|---|
| **InsForge** | Auth, roles (admin/host/user), Postgres data, private submissions, contests |
| **Nebius** | Inference engine every harness calls |
| **You.com** | Research Agent problem — live web search API |
| **Replit** | Host the judge/runner service |

## Problems

| Problem | Kind | Sponsor | What you engineer |
|---|---|---|---|
| **Connect 4** | Head-to-head | Nebius | `move(view, llm)` — agent plays the game |
| **Research Agent** | Task | You.com | `research(question, search, llm)` — agent finds facts |
| **Coding Bench** | Task | Nebius | `solve(spec, llm)` — agent writes code (CodingAgentBench DNA) |

Each problem has **code** and **no-code** harness modes. No-code = pick a Nebius model + system prompt (safe, great for live demos).

## Roles & fairness

- **User** — join contests, submit harnesses, see leaderboards (scores only, never others' code)
- **Host** — create contests, review all submissions, file reports
- **Admin** — manage users, grant/revoke host

Submissions are **private by default**. Only owners + hosts/admins can read code.

## Run locally

**Backend** (FastAPI judge):
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # optional: NEBIUS_API_KEY, YOU_API_KEY
uvicorn app:app --port 8000
```

**Frontend** (Vite + React):
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

### Demo accounts
| Email | Password | Role |
|---|---|---|
| builder@arena.dev | build123 | user |
| host@arena.dev | host123 | host |
| admin@arena.dev | admin123 | admin |

Without API keys, Nebius + You.com run in **deterministic mock mode** — fully offline demo-safe.

## InsForge (production backend)

Schema + RLS policies: `insforge/schema.sql`

```bash
npx @insforge/cli login
npx @insforge/cli link
# apply schema, set INSFORGE_URL + INSFORGE_ANON_KEY in .env
```

Local SQLite is the fallback when InsForge env vars are unset.

## Architecture

```
frontend/          React UI — problems, contests, auth, leaderboards, submit
backend/
  problems/        Problem registry (connect4, research-agent, coding-bench)
  engine/          Game engine, LLM client, You.com search, task eval
  harness*.py      Code + no-code harness loaders
  store.py         SQLite (local) / InsForge adapter (hosted)
  auth.py          JWT auth + role guards
  app.py           FastAPI API
insforge/          Postgres schema for hosted deploy
```

## Pitch thesis (already visible on leaderboard)

- **LLM-Naive** loses to **HeuristicBot** on Connect 4 — raw LLM calls aren't enough
- **Search-Naive** underperforms **Search-Strong** on Research Agent — harness engineering matters
- **Coder-Naive** vs **Coder-Strong** on Coding Bench — same model, different harness, different pass-rate

Win, but win **cheaply**. That's tokens-per-correct — the same metric CodingAgentBench uses.
