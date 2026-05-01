from fastapi import APIRouter, Query, Request

from backend.app.schemas.auth import LoginRequest, LoginResponse, MeResponse, RegisterRequest, RegisterResponse
from backend.app.services.auth_service import get_current_user, login_user, register_user
from backend.app.services.rate_limit_service import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
def register(request: Request, payload: RegisterRequest):
    client_ip = request.client.host if request.client else None
    enforce_rate_limit(
        user_id=None,
        scope="auth_register",
        limit=10,
        window_seconds=60,
        bucket_key=client_ip,
    )
    return register_user(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )


@router.post("/login", response_model=LoginResponse)
def login(request: Request, payload: LoginRequest):
    client_ip = request.client.host if request.client else None
    enforce_rate_limit(
        user_id=None,
        scope="auth_login",
        limit=15,
        window_seconds=60,
        bucket_key=client_ip,
    )
    return login_user(email=payload.email, password=payload.password)


@router.get("/me", response_model=MeResponse)
def me(user_id: str = Query(...)):
    return get_current_user(user_id)
