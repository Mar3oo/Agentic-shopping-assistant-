from pydantic import BaseModel


class ComparisonRequest(BaseModel):
    message: str
