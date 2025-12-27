# app/middleware/security.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

# ============================================
# SECURITY HEADERS (KEEP THIS)
# ============================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline';"
        )
        
        # HSTS (HTTP Strict Transport Security)
        from app.config import settings
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


# ============================================
# REQUEST LOGGING (KEEP THIS)
# ============================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with sanitized data"""
    
    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}
    SENSITIVE_PARAMS = {"password", "token", "secret", "api_key"}
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request (sanitized)
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"in {process_time:.2f}s"
        )
        
        return response


# ============================================
# SUSPICIOUS ACTIVITY DETECTION (KEEP THIS)
# ============================================

from collections import defaultdict

class SuspiciousActivityMiddleware(BaseHTTPMiddleware):
    """Detect and block suspicious activities"""
    
    def __init__(self, app):
        super().__init__(app)
        self.failed_attempts = defaultdict(list)
        self.blocked_ips = set()
        self.max_failures = 10
        self.block_duration = 3600  # 1 hour
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "access_denied",
                    "message": "Your IP has been temporarily blocked due to suspicious activity."
                }
            )
        
        response = await call_next(request)
        
        # Track failed authentication attempts
        if response.status_code == 401:
            self.failed_attempts[client_ip].append(current_time)
            
            # Remove old failures
            self.failed_attempts[client_ip] = [
                t for t in self.failed_attempts[client_ip] 
                if current_time - t < self.block_duration
            ]
            
            # Block if too many failures
            if len(self.failed_attempts[client_ip]) >= self.max_failures:
                self.blocked_ips.add(client_ip)
                logger.error(f"IP blocked due to repeated failures: {client_ip}")
        
        return response