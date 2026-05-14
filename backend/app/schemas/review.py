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
