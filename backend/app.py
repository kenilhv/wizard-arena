"""Arena API — multi-problem competitive agent-harness engineering platform."""
from __future__ import annotations

import os
import time
import traceback
import uuid

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

from auth import (  # noqa: E402
    can_view_submission,
    get_current_user,
    make_token,
    require_admin,
    require_host,
    require_user,
    verify_password,
)
from engine.llm import AVAILABLE_MODELS  # noqa: E402
from problems import get_problem, list_problems  # noqa: E402
from problems.base import Entry  # noqa: E402
import store  # noqa: E402

app = FastAPI(title="Arena", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class LoginBody(BaseModel):
    email: str
    password: str


class RegisterBody(BaseModel):
    email: str
    password: str
    display_name: str = ""


class RoleBody(BaseModel):
    role: str = Field(..., pattern="^(user|host|admin)$")


class ContestBody(BaseModel):
    title: str
    problem_slug: str
    start_at: float
    end_at: float


class ReportBody(BaseModel):
    submission_id: str
    reason: str


@app.on_event("startup")
def _startup() -> None:
    store.init_db()
    if os.getenv("AUTO_SEED", "1") == "1":
        for p in list_problems():
            if store.latest_tournament(p.slug) is None:
                try:
                    _run(p.slug)
                except Exception:
                    traceback.print_exc()


def _entries(slug: str, contest_id: str | None = None) -> list[Entry]:
    p = get_problem(slug)
    return p.baselines() + store.valid_entries(slug, contest_id)


def _run(slug: str, contest_id: str | None = None) -> dict:
    p = get_problem(slug)
    if not p:
        raise HTTPException(404, "unknown problem")
    tid = uuid.uuid4().hex[:12]
    res = p.evaluate(_entries(slug, contest_id))
    store.save_tournament(tid, slug, res["kind"], res["standings"], res["runs"], contest_id)
    return {"tournament_id": tid, "standings": res["standings"], "run_count": len(res["runs"])}


def _leaderboard_payload(slug: str, contest_id: str | None) -> dict:
    t = store.latest_tournament(slug, contest_id)
    p = get_problem(slug)
    if not t:
        return {
            "tournament_id": None,
            "kind": p.kind if p else None,
            "standings": [],
            "matches": [],
            "task_runs": [],
            "contest_id": contest_id,
        }
    payload = {
        "tournament_id": t["id"],
        "kind": t["kind"],
        "standings": t["standings"],
        "contest_id": contest_id,
        "created_at": t["created_at"],
    }
    if t["kind"] == "h2h":
        payload["matches"] = store.matches_for_tournament(t["id"])
        payload["task_runs"] = []
    else:
        payload["matches"] = []
        payload["task_runs"] = store.task_runs_for_tournament(t["id"])
    return payload


# --- auth --------------------------------------------------------------
@app.post("/api/auth/login")
def login(body: LoginBody) -> dict:
    user = store.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "invalid email or password")
    token = make_token(user)
    return {
        "token": token,
        "user": {
            "id": user["id"], "email": user["email"],
            "display_name": user["display_name"], "role": user["role"],
        },
    }


@app.post("/api/auth/register")
def register(body: RegisterBody) -> dict:
    if store.get_user_by_email(body.email):
        raise HTTPException(409, "email already registered")
    user = store.create_user(body.email, body.password, body.display_name or body.email.split("@")[0])
    token = make_token(user)
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def me(user: dict = Depends(require_user)) -> dict:
    return user


@app.get("/api/admin/users")
def admin_users(_: dict = Depends(require_admin)) -> dict:
    return {"users": store.list_users()}


@app.patch("/api/admin/users/{uid}/role")
def admin_set_role(uid: str, body: RoleBody, _: dict = Depends(require_admin)) -> dict:
    if not store.set_user_role(uid, body.role):
        raise HTTPException(404, "user not found")
    return {"ok": True, "id": uid, "role": body.role}


# --- contests ----------------------------------------------------------
@app.get("/api/contests")
def contests(problem_slug: str | None = None) -> dict:
    now = time.time()
    items = []
    for c in store.list_contests(problem_slug):
        items.append({
            **c,
            "is_open": store.contest_is_open(c),
            "is_upcoming": c["start_at"] > now,
            "is_closed": c["end_at"] < now,
        })
    return {"contests": items}


@app.post("/api/contests")
def create_contest(body: ContestBody, user: dict = Depends(require_host)) -> dict:
    if not get_problem(body.problem_slug):
        raise HTTPException(400, "unknown problem")
    if body.end_at <= body.start_at:
        raise HTTPException(400, "end_at must be after start_at")
    return store.create_contest(body.title, body.problem_slug, body.start_at, body.end_at, user["id"])


# --- problems ----------------------------------------------------------
@app.get("/api/problems")
def problems(contest_id: str | None = None) -> dict:
    return {
        "problems": [
            {**p.meta(), "entries": len(_entries(p.slug, contest_id))}
            for p in list_problems()
        ]
    }


@app.get("/api/problem/{slug}")
def problem(slug: str) -> dict:
    p = get_problem(slug)
    if not p:
        raise HTTPException(404, "unknown problem")
    return {
        **p.meta(),
        "template": p.template(),
        "models": AVAILABLE_MODELS,
        "llm_mock": not bool(os.getenv("NEBIUS_API_KEY")),
        "search_mock": not bool(os.getenv("YOU_API_KEY")),
    }


@app.get("/api/leaderboard/{slug}")
def leaderboard(slug: str, contest_id: str | None = None) -> dict:
    if not get_problem(slug):
        raise HTTPException(404, "unknown problem")
    return _leaderboard_payload(slug, contest_id)


# --- submissions (private code) ----------------------------------------
@app.post("/api/submit")
def submit(
    problem_slug: str = Form(...),
    mode: str = Form("code"),
    name: str = Form(...),
    author: str = Form("anon"),
    code: str = Form(""),
    model: str = Form("mock"),
    system_prompt: str = Form(""),
    temperature: float = Form(0.2),
    auto_guard: bool = Form(True),
    contest_id: str = Form(""),
    user: dict = Depends(require_user),
) -> dict:
    p = get_problem(problem_slug)
    if not p:
        raise HTTPException(404, "unknown problem")

    cid = contest_id.strip() or None
    if cid:
        contest = store.get_contest(cid)
        if not contest:
            raise HTTPException(404, "contest not found")
        if contest["problem_slug"] != problem_slug:
            raise HTTPException(400, "contest problem mismatch")
        if not store.contest_is_open(contest):
            raise HTTPException(403, "contest is not open for submissions")

    sid = "sub-" + uuid.uuid4().hex[:8]
    author_name = user.get("display_name") or author

    if mode == "nocode":
        if not p.supports_nocode:
            raise HTTPException(400, "this problem does not support no-code harnesses")
        nocode = {
            "model": model, "system_prompt": system_prompt,
            "temperature": temperature, "auto_guard": auto_guard,
        }
        store.save_submission(sid, problem_slug, name, author_name, "nocode", "pending",
                              nocode=nocode, user_id=user["id"], contest_id=cid)
        ok, err = p.validate(Entry(sid, name, author_name, nocode=nocode))
        store.save_submission(sid, problem_slug, name, author_name, "nocode",
                              "valid" if ok else "invalid", nocode=nocode, error=err,
                              user_id=user["id"], contest_id=cid)
        return {"id": sid, "valid": ok, "error": err}

    if not code.strip():
        raise HTTPException(400, "no harness code provided")
    path = store.save_submission(sid, problem_slug, name, author_name, "code", "pending",
                                 code=code, user_id=user["id"], contest_id=cid)
    ok, err = p.validate(Entry(sid, name, author_name, path=path))
    store.save_submission(sid, problem_slug, name, author_name, "code",
                          "valid" if ok else "invalid", code=code, error=err,
                          user_id=user["id"], contest_id=cid)
    return {"id": sid, "valid": ok, "error": err}


@app.get("/api/submission/{sid}")
def get_submission(
    sid: str,
    user: dict | None = Depends(get_current_user),
) -> dict:
    sub = store.get_submission(sid)
    if not sub:
        raise HTTPException(404, "submission not found")
    if not can_view_submission(user, sub):
        raise HTTPException(403, "submissions are private — you can only view your own")
    return sub


@app.get("/api/host/submissions")
def host_submissions(
    problem_slug: str | None = None,
    contest_id: str | None = None,
    _: dict = Depends(require_host),
) -> dict:
    return {"submissions": store.list_submissions_for_review(problem_slug, contest_id)}


@app.post("/api/host/report")
def host_report(body: ReportBody, user: dict = Depends(require_host)) -> dict:
    sub = store.get_submission(body.submission_id)
    if not sub:
        raise HTTPException(404, "submission not found")
    rid = store.save_report(body.submission_id, user["id"], body.reason)
    return {"id": rid, "ok": True}


@app.post("/api/tournament/run/{slug}")
def tournament_run(slug: str, contest_id: str | None = None) -> dict:
    return _run(slug, contest_id)


@app.get("/api/match/{mid}")
def match(mid: str) -> dict:
    m = store.get_match(mid)
    if not m:
        raise HTTPException(404, "match not found")
    return m


@app.get("/api/health")
def health() -> dict:
    from engine.search import active_provider
    provider = active_provider()
    return {
        "ok": True,
        "mock_llm": not bool(os.getenv("NEBIUS_API_KEY")),
        "mock_search": provider == "mock",
        "search_provider": provider,
        "insforge": __import__("insforge_client").health_ok(),
        "problems": [p.slug for p in list_problems()],
    }


# ── Serve the built frontend (single-service deploy, e.g. Replit) ──────
# In local dev the Vite server handles the UI and proxies /api here, so this
# block is a no-op until `frontend/dist` exists (i.e. after `npm run build`).
_DIST = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.isdir(_DIST):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    _ASSETS = os.path.join(_DIST, "assets")
    if os.path.isdir(_ASSETS):
        app.mount("/assets", StaticFiles(directory=_ASSETS), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # All /api routes are registered above and take precedence; everything
        # else falls through to the SPA (so client-side routes like
        # /problem/connect4 and /admin load index.html and hydrate).
        candidate = os.path.join(_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_DIST, "index.html"))
