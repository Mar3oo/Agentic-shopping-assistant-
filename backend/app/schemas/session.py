from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionSummary(BaseModel):
    session_id: str
    user_id: str
    agent_type: str
    status: str
    title: str | None = None
    last_sequence: int
    message_count: int
    version: int
    last_response_type: str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime


class SessionDetail(SessionSummary):
    agent_state: dict[str, Any] = Field(default_factory=dict)


class SessionMessage(BaseModel):
    message_id: str
    session_id: str
    user_id: str
    agent_type: str
    sequence: int
    role: str
    content: str
    payload: Any | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class SessionListData(BaseModel):
    sessions: list[SessionSummary]


class SessionDetailData(BaseModel):
    session: SessionDetail


class SessionMessagesData(BaseModel):
    messages: list[SessionMessage]


class SessionActionData(BaseModel):
    session_id: str
    status: str


class SessionListResponse(BaseModel):
    status: str
    message: str
    data: SessionListData


class SessionDetailResponse(BaseModel):
    status: str
    message: str
    data: SessionDetailData


class SessionMessagesResponse(BaseModel):
    status: str
    message: str
    data: SessionMessagesData


class SessionActionResponse(BaseModel):
    status: str
    message: str
    data: SessionActionData
