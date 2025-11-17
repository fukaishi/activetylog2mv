from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Activity Video Generator API",
    description="Generate videos from GPX/TCX/FIT activity files",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["videos"])


@app.get("/")
async def root():
    return {
        "message": "Activity Video Generator API",
        "version": "1.0.0",
        "docs": "/docs"
    }
