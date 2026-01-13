"""
FastAPI Application
Main application setup with middleware and error handlers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MQL5 Expert Advisor Generator API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": str(exc),
            "type": "ValueError"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
            "type": type(exc).__name__
        }
    )


# Import and include routes
from .routes import router
app.include_router(router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": "/api"
    }


# Health check
@app.get("/health")
async def health():
    import os
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "mt5_available": os.path.exists(settings.MT5_TERMINAL_PATH),
        "features": {
            "validation": True,
            "compilation": os.path.exists(settings.METAEDITOR_PATH),
            "backtesting": os.path.exists(settings.MT5_TERMINAL_PATH),
            "optimization": os.path.exists(settings.MT5_TERMINAL_PATH),
            "auto_improvement": True,
        }
    }
