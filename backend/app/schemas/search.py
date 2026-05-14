from typing import Any

from pydantic import BaseModel


class SearchRequest(BaseModel):
    user_id: str
    message: str
    language: str = "en"


class SearchResponse(BaseModel):
    status: str
    type: str
    message: str
    data: Any = None
