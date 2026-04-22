from pydantic import BaseModel


class SearchRequest(BaseModel):
    user_id: str
    message: str
