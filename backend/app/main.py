"""
LexiEase Backend - Main Application Entry Point

This module initializes the FastAPI application and defines
top-level routes. Feature-specific routes will be added as
separate 'routers' in later steps to keep this file clean.
"""
from fastapi import FastAPI
from app.database import supabase
# Create the FastAPI application instance
app = FastAPI(
    title="LexiEase API",
    description="AI-Powered Legal Document Simplifier and Risk Analyzer",
    version="0.1.0",)
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