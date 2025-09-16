import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from database import TORTOISE_ORM
from api import router as api_router
from auth_api import router as auth_router

app = FastAPI(
    title="File Tagger API",
    description="API for uploading, managing, and tagging files with simple CRUD operations",
    version="2.0.0"
)

register_tortoise(
    app,
    db_url=TORTOISE_ORM["connections"]["default"],
    modules={"models": TORTOISE_ORM["apps"]["models"]["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins.split(","),  # Frontend URLs from environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the File Tagger API!",
        "description": "Simple CRUD operations for files and collections with hierarchical organization",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"} 