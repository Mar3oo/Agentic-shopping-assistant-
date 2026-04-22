from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=80)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class AuthUserData(BaseModel):
    user_id: str
    mode: str
    email: str | None = None
    display_name: str | None = None


class RegisterResponse(BaseModel):
    status: str
    message: str
    data: AuthUserData


class LoginResponse(BaseModel):
    status: str
    message: str
    data: AuthUserData


class MeResponse(BaseModel):
    status: str
    message: str
    data: AuthUserData
