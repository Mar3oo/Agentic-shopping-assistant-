import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database.db import close_client, init_collections
from backend.app.routes import comparison, recommendation, review, search
from backend.app.routes.auth import router as auth_router
from backend.app.routes.session import router as session_router
from backend.app.routes.user import router as user_router
from backend.app.services.rate_limit_service import RateLimitExceeded

app = FastAPI(title="AI Shopping Assistant")

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_configured_origins = [
    origin.strip()
    for origin in os.getenv("SHOPPING_ASSISTANT_CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_configured_origins or _DEFAULT_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(recommendation.router)
app.include_router(comparison.router)
app.include_router(review.router)
app.include_router(search.router)


@app.exception_handler(RateLimitExceeded)
def rate_limit_exception_handler(_: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"status": "error", **exc.payload})


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or "Request failed"
        payload = {"status": "error", "message": message, **detail}
    else:
        payload = {"status": "error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.on_event("startup")
def startup_event():
    init_collections()


@app.on_event("shutdown")
def shutdown_event():
    close_client()


@app.get("/")
def health():
    return {"status": "ok"}
