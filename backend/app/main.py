"""
LexiEase Backend - Main Application Entry Point

This module initializes the FastAPI application and defines
top-level routes. Feature-specific routes will be added as
separate 'routers' in later steps to keep this file clean.
"""
from fastapi import FastAPI
from app.database import supabase
from app.dependencies.auth import get_current_user
from fastapi import FastAPI, Depends
from app.routers import documents
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents, pipeline
from app.routers import documents, pipeline, rag
from app.routers import documents, pipeline, rag, risk
from app.routers import documents, pipeline, rag, risk, history 

# Allow our frontend (running on a different port) to make
# requests to this backend. Without this, browsers block
# cross-origin requests by default for security reasons.

# Create the FastAPI application instance
app = FastAPI(
    title="LexiEase API",
    description="AI-Powered Legal Document Simplifier and Risk Analyzer",
    version="0.1.0",)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://lexiease-ai.vercel.app",
        "https://lexiease-gf5pgk2zo-the-insight-group.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(pipeline.router)
app.include_router(rag.router)
app.include_router(risk.router)
app.include_router(history.router)

@app.get("/")
async def root():
    """
    Root endpoint - confirms the API is reachable.
    Useful for quick manual checks.
    """
    return {"message": "Welcome to LexiEase API"}
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Deployment platforms (Render, etc.) ping this to verify
    the server is running correctly before routing traffic to it.
    """
    return {"status": "healthy", "service": "LexiEase Backend"}
@app.get("/test-db")
async def test_db_connection():
    """
    Temporary endpoint to verify Supabase connection is working.
    """
    try:
        buckets = supabase.storage.list_buckets()
        return {"connected": True, "buckets_found": len(buckets)}
    except Exception as e:
        return {"connected": False, "error": str(e)}

@app.get("/protected-test")
async def protected_test(current_user: dict = Depends(get_current_user)):
    """
    Temporary endpoint to verify backend JWT authentication works.
    Only accessible with a valid Supabase auth token.
    """
    return {
        "message": "You are authenticated!",
        "user_id": current_user["user_id"],
        "email": current_user["email"],
    }