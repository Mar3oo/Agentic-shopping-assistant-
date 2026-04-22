from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.session import (
    SessionActionResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionMessagesResponse,
)
from backend.app.services.session_service import (
    close_session_for_user,
    list_messages_for_session,
    list_sessions_for_user,
    load_session,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/", response_model=SessionListResponse)
def list_sessions(user_id: str = Query(...), limit: int = Query(20, ge=1, le=100)):
    return {
        "status": "success",
        "message": "Sessions retrieved",
        "data": {"sessions": list_sessions_for_user(user_id, limit=limit)},
    }


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str, user_id: str = Query(...)):
    session = load_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": "success",
        "message": "Session retrieved",
        "data": {"session": session},
    }


@router.get("/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_messages(
    session_id: str,
    user_id: str = Query(...),
    limit: int | None = Query(None, ge=1, le=500),
):
    session = load_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": "success",
        "message": "Messages retrieved",
        "data": {"messages": list_messages_for_session(user_id, session_id, limit=limit)},
    }


@router.post("/{session_id}/close", response_model=SessionActionResponse)
def close_session(session_id: str, user_id: str = Query(...)):
    session = load_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    close_session_for_user(user_id, session_id)
    return {
        "status": "success",
        "message": "Session closed",
        "data": {"session_id": session_id, "status": "closed"},
    }
