from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
import os
import hashlib
from tortoise.transactions import in_transaction
from models import Tree, Commit, Ref

from database import TORTOISE_ORM
from api import router as api_router

app = FastAPI(
    title="File Tagger API",
    description="API for uploading, managing, and tagging files",
    version="1.0.0"
)

register_tortoise(
    app,
    db_url=TORTOISE_ORM["connections"]["default"],
    modules={"models": TORTOISE_ORM["apps"]["models"]["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the File Tagger API!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def create_default_branch_and_commit():
    # Check if any commits exist
    if await Commit.exists():
        return

    async with in_transaction():
        # Create empty tree (hash of empty list)
        empty_tree = await Tree.create(entries=[])
        initial_commit = await Commit.create(
            tree=empty_tree,
            parent=None,
            message="Initial empty commit"
        )
        # Create 'main' branch ref
        await Ref.get_or_create(name="main", commit=initial_commit) 