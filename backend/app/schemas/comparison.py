from pydantic import BaseModel


class ComparisonStartRequest(BaseModel):
    user_id: str
    message: str


class ComparisonChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str