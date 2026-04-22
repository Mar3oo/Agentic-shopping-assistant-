from __future__ import annotations

import json
from typing import Any

import requests

from config import BACKEND_BASE_URL, REQUEST_TIMEOUT_SECONDS


class ApiClientError(Exception):
    pass


def _extract_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed with status {response.status_code}."

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            return detail.get("message") or json.dumps(detail)
        if isinstance(detail, str):
            return detail
        for key in ("message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(payload)

    return f"Request failed with status {response.status_code}."


def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{BACKEND_BASE_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_body,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ApiClientError(f"Could not connect to backend: {exc}") from exc

    if not response.ok:
        raise ApiClientError(_extract_error_message(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise ApiClientError("Backend returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise ApiClientError("Backend returned an unexpected response shape.")

    return payload


def create_guest_user() -> dict[str, Any]:
    return _request("POST", "/users/guest")


def register(email: str, password: str, display_name: str | None = None) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/register",
        json_body={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )


def login(email: str, password: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/auth/login",
        json_body={"email": email, "password": password},
    )


def get_current_user(user_id: str) -> dict[str, Any]:
    return _request("GET", "/auth/me", params={"user_id": user_id})


def start_recommendation(user_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/recommendation/start",
        json_body={"user_id": user_id, "message": message},
    )


def chat_recommendation(user_id: str, session_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/recommendation/chat",
        json_body={"user_id": user_id, "session_id": session_id, "message": message},
    )


def start_comparison(user_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/comparison/start",
        json_body={"user_id": user_id, "message": message},
    )


def chat_comparison(user_id: str, session_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/comparison/chat",
        json_body={"user_id": user_id, "session_id": session_id, "message": message},
    )


def start_review(user_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/review/start",
        json_body={"user_id": user_id, "message": message},
    )


def chat_review(user_id: str, session_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/review/chat",
        json_body={"user_id": user_id, "session_id": session_id, "message": message},
    )


def search(user_id: str, message: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/search/",
        json_body={"user_id": user_id, "message": message},
    )


def get_sessions(user_id: str, limit: int = 20) -> dict[str, Any]:
    return _request("GET", "/sessions/", params={"user_id": user_id, "limit": limit})


def get_session(session_id: str, user_id: str) -> dict[str, Any]:
    return _request("GET", f"/sessions/{session_id}", params={"user_id": user_id})


def get_session_messages(session_id: str, user_id: str, limit: int = 50) -> dict[str, Any]:
    return _request(
        "GET",
        f"/sessions/{session_id}/messages",
        params={"user_id": user_id, "limit": limit},
    )
