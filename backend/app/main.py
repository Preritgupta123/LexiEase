"""
LexiEase Backend - Main Application Entry Point

This module initializes the FastAPI application and defines
top-level routes. Feature-specific routes will be added as
separate 'routers' in later steps to keep this file clean.
"""
from fastapi import FastAPI, Request
import logging
import time
from app.database import supabase
from app.dependencies.auth import get_current_user
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents, pipeline, rag, risk, history 
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Allow our frontend (running on a different port) to make
# requests to this backend. Without this, browsers block
# cross-origin requests by default for security reasons.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

# Create the FastAPI application instance
app = FastAPI(
    title="LexiEase API",
    description="AI-Powered Legal Document Simplifier and Risk Analyzer",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://lexiease-ai.vercel.app",
    # "https://lexiease-gf5pgk2zo-the-insight-group.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to every response."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Process-Time"] = str(process_time)

    # ✅ Remove server info (don't advertise what you're running)
    response.headers.pop("Server", None)

    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests - especially auth failures."""
    response = await call_next(request)

    # Log suspicious activity
    if response.status_code == 401:
        logger.warning(
            f"UNAUTHORIZED: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
    elif response.status_code == 403:
        logger.warning(
            f"FORBIDDEN: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
    elif response.status_code >= 500:
        logger.error(
            f"SERVER ERROR: {request.method} {request.url.path} "
            f"status={response.status_code}"
        )

    return response

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