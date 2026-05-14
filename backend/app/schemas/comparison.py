from typing import Any

from pydantic import BaseModel


class ComparisonStartRequest(BaseModel):
    user_id: str
    message: str
    language: str = "en"


class ComparisonChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    language: str = "en"


class ComparisonResponse(BaseModel):
    status: str
    type: str
    message: str
    session_id: str | None = None
    data: Any = None
