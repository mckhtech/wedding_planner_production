from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import sys

from app.config import settings
from app.database import engine, Base
from app.api import auth, templates, generation, admin, test, payment, test_payment, contact
from app.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware, SuspiciousActivityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, RequestValidationMiddleware
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

# Create directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.GENERATED_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMPLATE_PREVIEW_DIR).mkdir(parents=True, exist_ok=True)
Path("app/templates").mkdir(parents=True, exist_ok=True)

# ============================================
# FASTAPI APP - Disable docs in production
# ============================================
app = FastAPI(
    title="Wedding Image Generator API",
    description="Pre-wedding image generation service",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ============================================
# MIDDLEWARE (ORDER MATTERS!)
# ============================================
# 1. Security Headers (must be first)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request Validation
app.add_middleware(RequestValidationMiddleware)

# 3. Rate Limiting
app.add_middleware(RateLimitMiddleware)

# 4. Suspicious Activity Detection
app.add_middleware(SuspiciousActivityMiddleware)

# 5. Request Logging
if not settings.is_production or settings.DEBUG:
    app.add_middleware(RequestLoggingMiddleware)

# 6. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 7. Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
    
    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred"}
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred",
            "detail": str(exc)
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
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    # Don't expose sensitive info in production
    return {
        "status": "healthy",
        "database": "connected"
    }

# ============================================
# STARTUP EVENT
# ============================================
@app.on_event("startup")
async def startup_event():
    directories = [
        settings.UPLOAD_DIR,
        settings.GENERATED_DIR,
        settings.TEMPLATE_PREVIEW_DIR
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directory ready: {directory}")
    
    logger.info(f"🚀 Application started")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔒 Production Mode: {settings.is_production}")
    logger.info(f"🌐 CORS Origins: {len(settings.cors_origins)} configured")
    logger.info(f"📄 API Docs: {'Disabled' if settings.is_production else 'Enabled at /docs'}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)