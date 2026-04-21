from pydantic import BaseModel


class ReviewRequest(BaseModel):
    message: str
