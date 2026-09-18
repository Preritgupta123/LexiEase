"""
LexiEase Backend - Main Application Entry Point

This module initializes the FastAPI application and defines
top-level routes. Feature-specific routes will be added as
separate 'routers' in later steps to keep this file clean.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import logging
import time

from app.database import supabase
from app.dependencies.auth import get_current_user
from fastapi import Depends
from app.routers import documents, pipeline, rag, risk, history 

# Allow our frontend (running on a different port) to make
# requests to this backend. Without this, browsers block
# cross-origin requests by default for security reasons.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

request_counts: dict = defaultdict(list)
RATE_LIMIT = 60        # Max requests
RATE_WINDOW = 60       # Per 60 seconds

def is_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded rate limit."""
    now = time.time()
    # Remove old requests outside window
    request_counts[ip] = [
        t for t in request_counts[ip]
        if now - t < RATE_WINDOW
    ]
    # Check limit
    if len(request_counts[ip]) >= RATE_LIMIT:
        return True
    # Add current request
    request_counts[ip].append(now)
    return False

# Create the FastAPI application instance
app = FastAPI(
    title="LexiEase API",
    description="AI-Powered Legal Document Simplifier and Risk Analyzer",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    )


ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://lexiease-ai.vercel.app",
    "https://lexiease-gf5pgk2zo-the-insight-group.vercel.app",
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
    max_age=600,  # Cache preflight for 10 minutes
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple IP-based rate limiting."""
    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health"]:
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"

    if is_rate_limited(ip):
        logger.warning(f"RATE LIMITED: {ip} on {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests. Please slow down."
            }
        )

    return await call_next(request)

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
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"  # HSTS - force HTTPS for 1 year
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://*.supabase.co https://lexiease-backend-vf27.onrender.com;"
    )
    response.headers["X-Process-Time"] = str(process_time)

    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log suspicious requests."""
    response = await call_next(request)

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
    elif response.status_code == 429:
        logger.warning(
            f"RATE LIMITED: {request.method} {request.url.path} "
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