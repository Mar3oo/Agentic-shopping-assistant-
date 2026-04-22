from pydantic import BaseModel


class GuestUserData(BaseModel):
    user_id: str
    mode: str


class GuestUserResponse(BaseModel):
    status: str
    message: str
    data: GuestUserData
