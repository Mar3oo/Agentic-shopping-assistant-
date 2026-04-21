from fastapi import FastAPI
from backend.app.routes import recommendation, comparison, review, search

app = FastAPI(title="AI Shopping Assistant")

# include router
app.include_router(recommendation.router)
app.include_router(comparison.router)
app.include_router(review.router)
app.include_router(search.router)


@app.get("/")
def health():
    return {"status": "ok"}
