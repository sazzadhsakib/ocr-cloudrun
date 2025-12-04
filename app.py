from fastapi import FastAPI
from src.api.v1.routes import router as api_router

app = FastAPI(
    title="OCR Cloud Run API",
    version="1.0.0"
)

# include versioned routes
app.include_router(api_router, prefix="/v1")
