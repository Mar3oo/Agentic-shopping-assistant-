from pydantic import BaseModel


class StartRequest(BaseModel):
    user_id: str
    message: str
    language: str = "en"


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str
    language: str = "en"
