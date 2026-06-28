"""Local JWT auth (demo) with InsForge-ready role model: admin | host | user."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("ARENA_JWT_SECRET", "arena-dev-secret-change-me")
TOKEN_TTL = int(os.getenv("ARENA_TOKEN_TTL", str(7 * 86400)))

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = "arena-v1"
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def make_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user.get("display_name") or user["email"],
        "exp": int(time.time()) + TOKEN_TTL,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(JWT_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_token(token: str) -> Optional[dict]:
    try:
        body, sig = token.rsplit(".", 1)
        expected = hmac.new(JWT_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        pad = "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(body + pad))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def decode_insforge_jwt(token: str) -> Optional[dict]:
    """Decode InsForge access JWT payload (signature verified by InsForge at issuance)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        pad = "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    if not creds or not creds.credentials:
        return None
    token = creds.credentials
    payload = decode_token(token)
    if payload:
        return {
            "id": payload["sub"],
            "email": payload.get("email", ""),
            "role": payload.get("role", "user"),
            "display_name": payload.get("name", ""),
        }
    # InsForge access token (JWT)
    if payload := decode_insforge_jwt(token):
        from insforge_client import get_profile
        uid = payload.get("sub") or payload.get("user_id")
        if not uid:
            return None
        profile = get_profile(str(uid))
        return {
            "id": str(uid),
            "email": payload.get("email", ""),
            "role": (profile or {}).get("role", "user"),
            "display_name": (profile or {}).get("display_name") or payload.get("email", ""),
        }
    return None


def require_user(user: Optional[dict] = Depends(get_current_user)) -> dict:
    if not user:
        raise HTTPException(401, "sign in required")
    return user


def require_host(user: dict = Depends(require_user)) -> dict:
    if user["role"] not in ("host", "admin"):
        raise HTTPException(403, "host or admin role required")
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "admin role required")
    return user


def can_view_submission(user: Optional[dict], submission: dict) -> bool:
    """Users see only their own code; hosts/admins see all."""
    if not user:
        return False
    if user["role"] in ("admin", "host"):
        return True
    return submission.get("user_id") == user["id"]


def new_user_id() -> str:
    return "usr-" + uuid.uuid4().hex[:10]
