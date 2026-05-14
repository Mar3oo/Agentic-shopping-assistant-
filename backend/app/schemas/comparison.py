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
