from pydantic import BaseModel


class SearchRequest(BaseModel):
    message: str
