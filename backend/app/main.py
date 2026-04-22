from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from Data_Base.db import close_client, init_collections
from backend.app.routes import comparison, recommendation, review, search
from backend.app.routes.auth import router as auth_router
from backend.app.routes.session import router as session_router
from backend.app.routes.user import router as user_router
from backend.app.services.rate_limit_service import RateLimitExceeded

app = FastAPI(title="AI Shopping Assistant")

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(recommendation.router)
app.include_router(comparison.router)
app.include_router(review.router)
app.include_router(search.router)


@app.exception_handler(RateLimitExceeded)
def rate_limit_exception_handler(_: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content=exc.payload)


@app.on_event("startup")
def startup_event():
    init_collections()


@app.on_event("shutdown")
def shutdown_event():
    close_client()


@app.get("/")
def health():
    return {"status": "ok"}
