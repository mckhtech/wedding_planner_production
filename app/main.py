from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import sys
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, check_db_connection, get_pool_status
from app.api import auth, templates, generation, admin, test, payment, test_payment, contact
import app.models

# ============================================
# LOGGING CONFIGURATION
# ============================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log') if settings.is_production else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.GENERATED_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMPLATE_PREVIEW_DIR).mkdir(parents=True, exist_ok=True)

Path("app/templates").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Wedding Image Generator API",
    description="Pre-wedding image generation service",
    version="1.0.0"
)

# ============================================
# CORS MIDDLEWARE - Uses .env ALLOWED_ORIGINS
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# DEBUG MIDDLEWARE - Logs CORS requests (optional, remove in production)
# ============================================
@app.middleware("http")
async def log_cors_requests(request: Request, call_next):
    """Log incoming requests for debugging CORS issues"""
    origin = request.headers.get('origin')
    if origin:
        logger.info(f"🌐 Request from origin: {origin}")
        logger.info(f"📍 Method: {request.method} | Path: {request.url.path}")
    
    response = await call_next(request)
    
    # Log CORS headers in response
    if origin:
        logger.info(f"✅ CORS headers sent: {response.headers.get('access-control-allow-origin')}")
    
    return response

# ============================================
# STATIC FILE MOUNTS
# ============================================
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=settings.GENERATED_DIR), name="generated")
app.mount("/template_previews", StaticFiles(directory=settings.TEMPLATE_PREVIEW_DIR), name="template_previews")

# ============================================
# ROUTER INCLUDES
# ============================================
app.include_router(auth.router)
app.include_router(templates.router)
app.include_router(generation.router)
app.include_router(admin.router)
app.include_router(payment.router)
app.include_router(test.router)
app.include_router(test_payment.router)
app.include_router(contact.router)

# ============================================
# EXCEPTION HANDLERS
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.DEBUG else "Internal server error"
        }
    )

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================
@app.get("/")
async def root():
    return {
        "message": "Wedding Image Generator API",
        "status": "running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.ENVIRONMENT
    }

# ============================================
# STARTUP EVENT
# ============================================
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    directories = [
        settings.UPLOAD_DIR,
        settings.GENERATED_DIR,
        settings.TEMPLATE_PREVIEW_DIR
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directory ready: {directory}")
    
    # Log CORS configuration
    logger.info(f"🌐 CORS Origins: {settings.cors_origins}")
    logger.info(f"🚀 Application started successfully")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔒 Debug mode: {settings.DEBUG}")

# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)