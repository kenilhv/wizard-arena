"""InsForge server-side client (service key) for profiles, submissions, contests, reports."""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

INSFORGE_URL = os.getenv("INSFORGE_URL", os.getenv("INSFORGE_API_BASE_URL", "")).rstrip("/")
INSFORGE_API_KEY = os.getenv("INSFORGE_API_KEY", os.getenv("INSFORGE_ANON_KEY", ""))

_submissions_flowing = False
_connected: Optional[bool] = None


def enabled() -> bool:
    return bool(INSFORGE_URL and INSFORGE_API_KEY)


def submissions_flowing() -> bool:
    return bool(enabled() and _submissions_flowing)


def _headers(prefer: str | None = None) -> dict[str, str]:
    h = {
        "Authorization": f"Bearer {INSFORGE_API_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _rows(resp: httpx.Response) -> list[dict[str, Any]]:
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return list(data.get("data") or data.get("records") or [])
    return list(data) if isinstance(data, list) else []


def _ts(val: Any) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.replace("Z", "+00:00")
        return datetime.fromisoformat(s).timestamp()
    return 0.0


def check_connection() -> bool:
    """Verify InsForge database API is reachable (cached after first success)."""
    global _connected
    if not enabled():
        return False
    if _connected is True:
        return True
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/submissions",
            headers=_headers(),
            params={"limit": 1},
            timeout=8.0,
        )
        resp.raise_for_status()
        _connected = True
        return True
    except Exception:
        _connected = False
        return False


def get_profile(user_id: str) -> Optional[dict[str, Any]]:
    if not enabled():
        return None
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/profiles",
            headers=_headers(),
            params={"id": f"eq.{user_id}", "limit": 1},
            timeout=10.0,
        )
        rows = _rows(resp)
        return rows[0] if rows else None
    except Exception:
        return None


def upsert_submission(row: dict[str, Any]) -> bool:
    global _submissions_flowing
    if not enabled():
        return False
    try:
        resp = httpx.post(
            f"{INSFORGE_URL}/api/database/records/submissions",
            headers=_headers("resolution=merge-duplicates,return=representation"),
            json=row,
            timeout=15.0,
        )
        _rows(resp)
        _submissions_flowing = True
        _connected = True
        return True
    except Exception:
        return False


def get_submission(sid: str) -> Optional[dict[str, Any]]:
    if not enabled():
        return None
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/submissions",
            headers=_headers(),
            params={"id": f"eq.{sid}", "limit": 1},
            timeout=10.0,
        )
        rows = _rows(resp)
        return _normalize_submission(rows[0]) if rows else None
    except Exception:
        return None


def list_submissions(
    problem_slug: Optional[str] = None,
    contest_id: Optional[str] = None,
    status: Optional[str] = None,
    include_code: bool = False,
) -> list[dict[str, Any]]:
    if not enabled():
        return []
    params: dict[str, str] = {"order": "created_at.desc", "limit": "200"}
    if problem_slug:
        params["problem_slug"] = f"eq.{problem_slug}"
    if contest_id:
        params["contest_id"] = f"eq.{contest_id}"
    if status:
        params["status"] = f"eq.{status}"
    if not include_code:
        params["select"] = (
            "id,problem_slug,name,mode,status,user_id,contest_id,created_at,error"
        )
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/submissions",
            headers=_headers(),
            params=params,
            timeout=15.0,
        )
        return [_normalize_submission(r) for r in _rows(resp)]
    except Exception:
        return []


def list_valid_submissions(
    problem_slug: str, contest_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "problem_slug": f"eq.{problem_slug}",
        "status": "eq.valid",
        "order": "created_at.asc",
        "limit": "500",
    }
    if contest_id:
        params["contest_id"] = f"eq.{contest_id}"
    else:
        params["contest_id"] = "is.null"
    if not enabled():
        return []
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/submissions",
            headers=_headers(),
            params=params,
            timeout=15.0,
        )
        return [_normalize_submission(r) for r in _rows(resp)]
    except Exception:
        return []


def _normalize_submission(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if out.get("created_at"):
        out["created_at"] = _ts(out["created_at"])
    profile = get_profile(str(out["user_id"])) if out.get("user_id") else None
    out["author"] = (profile or {}).get("display_name") or out.get("name") or "anon"
    return out


def sync_submission(
    *,
    sid: str,
    problem_slug: str,
    name: str,
    user_id: str,
    mode: str,
    status: str,
    code: str = "",
    nocode: Optional[dict] = None,
    error: str = "",
    contest_id: Optional[str] = None,
) -> bool:
    row: dict[str, Any] = {
        "id": sid,
        "problem_slug": problem_slug,
        "user_id": user_id,
        "name": name,
        "mode": mode,
        "status": status,
        "error": error or None,
    }
    if contest_id:
        row["contest_id"] = contest_id
    if mode == "code":
        row["code"] = code
        row["nocode"] = None
    else:
        row["code"] = None
        row["nocode"] = nocode
    return upsert_submission(row)


def list_contests(problem_slug: Optional[str] = None) -> list[dict[str, Any]]:
    if not enabled():
        return []
    params: dict[str, str] = {"order": "start_at.asc", "limit": "100"}
    if problem_slug:
        params["problem_slug"] = f"eq.{problem_slug}"
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/contests",
            headers=_headers(),
            params=params,
            timeout=10.0,
        )
        out = []
        for r in _rows(resp):
            out.append({
                **r,
                "start_at": _ts(r.get("start_at")),
                "end_at": _ts(r.get("end_at")),
                "created_at": _ts(r.get("created_at")) if r.get("created_at") else time.time(),
            })
        return out
    except Exception:
        return []


def get_contest(cid: str) -> Optional[dict[str, Any]]:
    if not enabled():
        return None
    try:
        resp = httpx.get(
            f"{INSFORGE_URL}/api/database/records/contests",
            headers=_headers(),
            params={"id": f"eq.{cid}", "limit": 1},
            timeout=10.0,
        )
        rows = _rows(resp)
        if not rows:
            return None
        r = rows[0]
        return {
            **r,
            "start_at": _ts(r.get("start_at")),
            "end_at": _ts(r.get("end_at")),
        }
    except Exception:
        return None


def save_report(submission_id: str, reporter_id: str, reason: str) -> Optional[str]:
    if not enabled():
        return None
    rid = "rpt-" + uuid.uuid4().hex[:8]
    try:
        resp = httpx.post(
            f"{INSFORGE_URL}/api/database/records/reports",
            headers=_headers("return=representation"),
            json={
                "id": rid,
                "submission_id": submission_id,
                "reporter_id": reporter_id,
                "reason": reason,
            },
            timeout=10.0,
        )
        _rows(resp)
        return rid
    except Exception:
        return None


def health_ok() -> bool:
    """True when InsForge is configured and submission sync is working or verified reachable."""
    if not enabled():
        return False
    if _submissions_flowing:
        return True
    return check_connection()
