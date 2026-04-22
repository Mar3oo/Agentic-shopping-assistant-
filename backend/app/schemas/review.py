from pydantic import BaseModel


class ReviewStartRequest(BaseModel):
    user_id: str
    message: str


class ReviewChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
