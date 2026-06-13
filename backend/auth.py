"""Lightweight file-backed auth for EchoEcho.

Stores users in backend/users.json with SHA-256 password hashes and is seeded
with the demo account (test@echo.com / test@123). Tokens are opaque random
strings — enough for the demo's localStorage-based session handling.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"

DEMO_EMAIL = "test@echo.com"
DEMO_PASSWORD = "test@123"
DEMO_NAME = "Echo Tester"

_users_lock = Lock()


class AuthError(ValueError):
    pass


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _seed_users() -> dict[str, dict[str, str]]:
    return {DEMO_EMAIL: {"name": DEMO_NAME, "password_hash": _hash_password(DEMO_PASSWORD)}}


def _read_users() -> dict[str, dict[str, str]]:
    if not USERS_FILE.exists():
        users = _seed_users()
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
        return users
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        data = {}
    if DEMO_EMAIL not in data:
        data.update(_seed_users())
        USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _issue_session(email: str, name: str) -> dict[str, object]:
    return {
        "ok": True,
        "token": secrets.token_hex(24),
        "user": {"name": name, "email": email},
    }


def login(email: str, password: str) -> dict[str, object]:
    normalized = email.strip().lower()
    with _users_lock:
        user = _read_users().get(normalized)
    if not user or user.get("password_hash") != _hash_password(password):
        raise AuthError("Invalid email or password.")
    return _issue_session(normalized, str(user.get("name") or normalized.split("@")[0].title()))


def signup(name: str, email: str, password: str) -> dict[str, object]:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise AuthError("Please enter a valid email address.")
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")
    display_name = name.strip() or normalized.split("@")[0].replace(".", " ").title()
    with _users_lock:
        users = _read_users()
        if normalized in users:
            raise AuthError("An account with this email already exists.")
        users[normalized] = {"name": display_name, "password_hash": _hash_password(password)}
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    return _issue_session(normalized, display_name)
