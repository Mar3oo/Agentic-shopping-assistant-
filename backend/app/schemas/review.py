from typing import Any

from pydantic import BaseModel


class ReviewStartRequest(BaseModel):
    user_id: str
    message: str
    language: str = "en"


class ReviewChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    language: str = "en"


class ReviewResponse(BaseModel):
    status: str
    type: str
    message: str
    session_id: str | None = None
    data: Any = None
