"""Local SQLite store (problem-scoped). InsForge adapter mirrors this schema
for the hosted multi-user platform — see insforge/schema.sql."""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional

from auth import hash_password, new_user_id
from problems.base import Entry

try:
    import insforge_client as ifc
except ImportError:
    ifc = None  # type: ignore[assignment]

DB_PATH = os.path.join(os.path.dirname(__file__), "arena.db")
SUBMISSION_DIR = os.path.join(os.path.dirname(__file__), "submissions")
os.makedirs(SUBMISSION_DIR, exist_ok=True)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _add_column(c: sqlite3.Connection, table: str, col: str, typedef: str) -> None:
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")
    except sqlite3.OperationalError:
        pass


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT UNIQUE, display_name TEXT,
                password_hash TEXT, role TEXT DEFAULT 'user', created_at REAL
            );
            CREATE TABLE IF NOT EXISTS contests (
                id TEXT PRIMARY KEY, title TEXT, problem_slug TEXT,
                start_at REAL, end_at REAL, status TEXT, host_id TEXT, created_at REAL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, submission_id TEXT, reporter_id TEXT,
                reason TEXT, created_at REAL
            );
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY, problem_slug TEXT, name TEXT, author TEXT,
                mode TEXT, code TEXT, nocode TEXT, path TEXT,
                status TEXT, error TEXT, created_at REAL
            );
            CREATE TABLE IF NOT EXISTS tournaments (
                id TEXT PRIMARY KEY, problem_slug TEXT, standings TEXT, kind TEXT,
                created_at REAL
            );
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY, tournament_id TEXT, problem_slug TEXT,
                name_a TEXT, name_b TEXT, entry_a TEXT, entry_b TEXT,
                winner TEXT, reason TEXT, moves TEXT, frames TEXT,
                usage TEXT, created_at REAL
            );
            CREATE TABLE IF NOT EXISTS task_runs (
                id TEXT PRIMARY KEY, tournament_id TEXT, problem_slug TEXT,
                entry_id TEXT, entry_name TEXT, task_id TEXT, task_label TEXT,
                correct INTEGER, detail TEXT, usage TEXT, created_at REAL
            );
            """
        )
        _add_column(c, "submissions", "user_id", "TEXT")
        _add_column(c, "submissions", "contest_id", "TEXT")
        _add_column(c, "tournaments", "contest_id", "TEXT")
    seed_users()
    seed_contests()


def seed_users() -> None:
    demos = [
        ("admin@arena.dev", "Arena Admin", "admin", "admin123"),
        ("host@arena.dev", "Contest Host", "host", "host123"),
        ("builder@arena.dev", "Demo Builder", "user", "build123"),
    ]
    with _conn() as c:
        for email, name, role, pw in demos:
            row = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if row:
                continue
            c.execute(
                "INSERT INTO users (id, email, display_name, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
                (new_user_id(), email, name, hash_password(pw), role, time.time()),
            )


def seed_contests() -> None:
    """Demo timed contest — June 30 2026 12:30–14:00 PDT (unix timestamps)."""
    import datetime as dt
    start = dt.datetime(2026, 6, 30, 12, 30, tzinfo=dt.timezone(dt.timedelta(hours=-7)))
    end = dt.datetime(2026, 6, 30, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=-7)))
    with _conn() as c:
        row = c.execute("SELECT id FROM contests LIMIT 1").fetchone()
        if row:
            return
        host = c.execute("SELECT id FROM users WHERE role='host' LIMIT 1").fetchone()
        host_id = host["id"] if host else None
        c.execute(
            "INSERT INTO contests VALUES (?,?,?,?,?,?,?,?)",
            ("contest-wizard-demo", "Wizard Sprint — Connect 4", "connect4",
             start.timestamp(), end.timestamp(), "scheduled", host_id, time.time()),
        )
        c.execute(
            "INSERT INTO contests VALUES (?,?,?,?,?,?,?,?)",
            ("contest-research-july", "Research Agent Showdown", "research-agent",
             start.timestamp() + 86400, end.timestamp() + 86400, "scheduled", host_id, time.time()),
        )


# --- users / auth ------------------------------------------------------
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
    return dict(row) if row else None


def get_user(uid: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None


def create_user(email: str, password: str, display_name: str, role: str = "user") -> dict:
    uid = new_user_id()
    with _conn() as c:
        c.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?)",
            (uid, email.lower(), display_name, hash_password(password), role, time.time()),
        )
    return {"id": uid, "email": email.lower(), "display_name": display_name, "role": role}


def set_user_role(uid: str, role: str) -> bool:
    with _conn() as c:
        cur = c.execute("UPDATE users SET role=? WHERE id=?", (role, uid))
        return cur.rowcount > 0


def list_users() -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, email, display_name, role, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def _insforge_on() -> bool:
    return bool(ifc and ifc.enabled())


# --- contests ----------------------------------------------------------
def list_contests(problem_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    if _insforge_on():
        return ifc.list_contests(problem_slug)
    with _conn() as c:
        if problem_slug:
            rows = c.execute(
                "SELECT * FROM contests WHERE problem_slug=? ORDER BY start_at", (problem_slug,)
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM contests ORDER BY start_at").fetchall()
    return [dict(r) for r in rows]


def get_contest(cid: str) -> Optional[Dict[str, Any]]:
    if _insforge_on():
        return ifc.get_contest(cid)
    with _conn() as c:
        row = c.execute("SELECT * FROM contests WHERE id=?", (cid,)).fetchone()
    return dict(row) if row else None


def contest_is_open(contest: dict) -> bool:
    now = time.time()
    return contest["start_at"] <= now <= contest["end_at"]


def create_contest(title: str, problem_slug: str, start_at: float, end_at: float,
                   host_id: str) -> dict:
    cid = "contest-" + uuid.uuid4().hex[:8]
    with _conn() as c:
        c.execute(
            "INSERT INTO contests VALUES (?,?,?,?,?,?,?,?)",
            (cid, title, problem_slug, start_at, end_at, "scheduled", host_id, time.time()),
        )
    return get_contest(cid)  # type: ignore[return-value]


# --- submissions -------------------------------------------------------
def save_submission(
    sid: str, problem_slug: str, name: str, author: str,
    mode: str, status: str, code: str = "",
    nocode: Optional[dict] = None, error: str = "",
    user_id: Optional[str] = None, contest_id: Optional[str] = None,
) -> str:
    path = ""
    if mode == "code":
        path = os.path.join(SUBMISSION_DIR, f"{sid}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO submissions "
            "(id, problem_slug, name, author, mode, code, nocode, path, status, error, created_at, user_id, contest_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, problem_slug, name, author, mode, code,
             json.dumps(nocode) if nocode else None, path, status, error, time.time(),
             user_id, contest_id),
        )
    if _insforge_on() and user_id:
        ifc.sync_submission(
            sid=sid, problem_slug=problem_slug, name=name, user_id=user_id,
            mode=mode, status=status, code=code, nocode=nocode, error=error,
            contest_id=contest_id,
        )
    return path


def _ensure_code_file(sid: str, code: str) -> str:
    path = os.path.join(SUBMISSION_DIR, f"{sid}.py")
    if code:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
    return path


def valid_entries(problem_slug: str, contest_id: Optional[str] = None) -> List[Entry]:
    if _insforge_on():
        rows = ifc.list_valid_submissions(problem_slug, contest_id)
        out: List[Entry] = []
        for r in rows:
            author = r.get("author") or r.get("name") or "anon"
            if r["mode"] == "nocode":
                nc = r.get("nocode")
                if isinstance(nc, str):
                    nc = json.loads(nc)
                out.append(Entry(r["id"], r["name"], author, nocode=nc))
            else:
                path = _ensure_code_file(r["id"], r.get("code") or "")
                out.append(Entry(r["id"], r["name"], author, path=path))
        return out
    with _conn() as c:
        if contest_id:
            rows = c.execute(
                "SELECT * FROM submissions WHERE problem_slug=? AND status='valid' AND contest_id=?",
                (problem_slug, contest_id),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM submissions WHERE problem_slug=? AND status='valid' AND contest_id IS NULL",
                (problem_slug,),
            ).fetchall()
    out = []
    for r in rows:
        if r["mode"] == "nocode":
            out.append(Entry(r["id"], r["name"], r["author"], nocode=json.loads(r["nocode"])))
        else:
            out.append(Entry(r["id"], r["name"], r["author"], path=r["path"]))
    return out


def get_submission(sid: str) -> Optional[Dict[str, Any]]:
    if _insforge_on():
        row = ifc.get_submission(sid)
        if row:
            if row.get("mode") == "nocode" and isinstance(row.get("nocode"), str):
                row["nocode"] = json.loads(row["nocode"])
            return row
        return None
    with _conn() as c:
        row = c.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    return dict(row) if row else None


def list_submissions_for_review(problem_slug: Optional[str] = None,
                                contest_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Host/admin review list — includes full code for moderation."""
    if _insforge_on():
        rows = ifc.list_submissions(problem_slug, contest_id, include_code=True)
        for r in rows:
            if r.get("mode") == "nocode" and isinstance(r.get("nocode"), str):
                r["nocode"] = json.loads(r["nocode"])
        return rows
    q = (
        "SELECT id, problem_slug, name, author, mode, status, user_id, contest_id, "
        "created_at, error, code, nocode FROM submissions WHERE 1=1"
    )
    params: list = []
    if problem_slug:
        q += " AND problem_slug=?"
        params.append(problem_slug)
    if contest_id:
        q += " AND contest_id=?"
        params.append(contest_id)
    q += " ORDER BY created_at DESC"
    with _conn() as c:
        rows = c.execute(q, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("nocode"):
            d["nocode"] = json.loads(d["nocode"])
        out.append(d)
    return out


def save_report(submission_id: str, reporter_id: str, reason: str) -> str:
    if _insforge_on():
        rid = ifc.save_report(submission_id, reporter_id, reason)
        if rid:
            return rid
    rid = "rpt-" + uuid.uuid4().hex[:8]
    with _conn() as c:
        c.execute(
            "INSERT INTO reports VALUES (?,?,?,?,?)",
            (rid, submission_id, reporter_id, reason, time.time()),
        )
    return rid


# --- tournaments / matches / task runs ---------------------------------
def save_tournament(
    tid: str, problem_slug: str, kind: str,
    standings: List[Dict[str, Any]], runs: List[Dict[str, Any]],
    contest_id: Optional[str] = None,
) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO tournaments (id, problem_slug, standings, kind, created_at, contest_id) "
            "VALUES (?,?,?,?,?,?)",
            (tid, problem_slug, json.dumps(standings), kind, time.time(), contest_id),
        )
        if kind == "h2h":
            for m in runs:
                c.execute(
                    "INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (m["id"], tid, problem_slug, m["names"]["A"], m["names"]["B"],
                     m["entry_ids"]["A"], m["entry_ids"]["B"], m["winner"], m["reason"],
                     json.dumps(m["moves"]), json.dumps(m["frames"]),
                     json.dumps(m["usage"]), time.time()),
                )
        else:
            for r in runs:
                c.execute(
                    "INSERT OR REPLACE INTO task_runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (r["id"], tid, problem_slug, r["entry_id"], r["entry_name"],
                     r.get("task_id"), r.get("task_label"), int(r["correct"]),
                     r.get("detail", ""), json.dumps(r.get("usage", {})), time.time()),
                )


def latest_tournament(problem_slug: str, contest_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        if contest_id:
            row = c.execute(
                "SELECT * FROM tournaments WHERE problem_slug=? AND contest_id=? "
                "ORDER BY created_at DESC LIMIT 1",
                (problem_slug, contest_id),
            ).fetchone()
        else:
            row = c.execute(
                "SELECT * FROM tournaments WHERE problem_slug=? AND contest_id IS NULL "
                "ORDER BY created_at DESC LIMIT 1",
                (problem_slug,),
            ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"], "problem_slug": problem_slug, "kind": row["kind"],
        "standings": json.loads(row["standings"]), "created_at": row["created_at"],
        "contest_id": row["contest_id"] if "contest_id" in row.keys() else None,
    }


def matches_for_tournament(tid: str) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name_a, name_b, entry_a, entry_b, winner, reason "
            "FROM matches WHERE tournament_id=? ORDER BY created_at", (tid,),
        ).fetchall()
    return [dict(r) for r in rows]


def task_runs_for_tournament(tid: str) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, entry_id, entry_name, task_id, task_label, correct, detail "
            "FROM task_runs WHERE tournament_id=? ORDER BY created_at", (tid,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_match(mid: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM matches WHERE id=?", (mid,)).fetchone()
    if not row:
        return None
    return {
        "id": row["id"], "names": {"A": row["name_a"], "B": row["name_b"]},
        "entry_ids": {"A": row["entry_a"], "B": row["entry_b"]},
        "winner": row["winner"], "reason": row["reason"],
        "moves": json.loads(row["moves"]), "frames": json.loads(row["frames"]),
        "usage": json.loads(row["usage"]),
    }
