from fastapi import APIRouter, Request

from backend.app.schemas.user import GuestUserResponse
from backend.app.services.rate_limit_service import enforce_rate_limit
from backend.app.services.user_service import create_guest_user_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/guest", response_model=GuestUserResponse)
def create_guest(request: Request):
    client_ip = request.client.host if request.client else None
    enforce_rate_limit(
        user_id=None,
        scope="guest_user",
        limit=20,
        window_seconds=60,
        bucket_key=client_ip,
    )
    return create_guest_user_response()
