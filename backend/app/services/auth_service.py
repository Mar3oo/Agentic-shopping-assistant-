import base64
import hashlib
import hmac
import os
import re

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from Data_Base.user_repo import (
    create_registered_user,
    get_user,
    get_user_by_email,
    update_last_seen,
)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 64


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _validate_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not _EMAIL_PATTERN.match(normalized):
        raise HTTPException(status_code=400, detail="Invalid email address")
    return normalized


def _validate_password(password: str) -> str:
    candidate = password or ""
    if len(candidate) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )
    return candidate


def hash_password(password: str) -> str:
    validated = _validate_password(password)
    salt = os.urandom(16)
    derived_key = hashlib.scrypt(
        validated.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    key_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt_b64}${key_b64}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    try:
        algorithm, n, r, p, salt_b64, key_b64 = stored_hash.split("$", maxsplit=5)
        if algorithm != "scrypt":
            return False

        expected_key = base64.b64decode(key_b64.encode("ascii"))
        derived_key = hashlib.scrypt(
            _validate_password(password).encode("utf-8"),
            salt=base64.b64decode(salt_b64.encode("ascii")),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected_key),
        )
    except Exception:
        return False

    return hmac.compare_digest(derived_key, expected_key)


def _auth_user_payload(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "mode": user["mode"],
        "email": user.get("email"),
        "display_name": user.get("display_name"),
    }


def register_user(email: str, password: str, display_name: str | None = None) -> dict:
    normalized_email = _validate_email(email)
    if get_user_by_email(normalized_email):
        raise HTTPException(status_code=409, detail="Email is already registered")

    try:
        user = create_registered_user(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email is already registered")

    return {
        "status": "success",
        "message": "User registered successfully",
        "data": _auth_user_payload(user),
    }


def login_user(email: str, password: str) -> dict:
    normalized_email = _validate_email(email)
    user = get_user_by_email(normalized_email)

    if not user or user.get("mode") != "registered":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is inactive")
    if not verify_password(password, user.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    updated_user = update_last_seen(user["user_id"]) or user
    return {
        "status": "success",
        "message": "Login successful",
        "data": _auth_user_payload(updated_user),
    }


def get_current_user(user_id: str) -> dict:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is inactive")

    return {
        "status": "success",
        "message": "User retrieved",
        "data": _auth_user_payload(user),
    }
