import re
import html
from typing import Optional
from fastapi import HTTPException

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent XSS"""
    if not value:
        return value
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # HTML escape to prevent XSS
    value = html.escape(value)
    
    # Limit length
    if len(value) > max_length:
        raise HTTPException(status_code=400, detail=f"Input too long (max {max_length} characters)")
    
    return value.strip()

def validate_email(email: str) -> str:
    """Validate and sanitize email"""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    email = sanitize_string(email, max_length=255)
    
    # Email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    return email.lower()

def detect_sql_injection(value: str) -> bool:
    """Detect potential SQL injection attempts"""
    if not value:
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\bOR\b|\bAND\b)\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?",
        r"UNION\s+SELECT",
        r"INSERT\s+INTO",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
        r"--\s*$",
        r";\s*--",
        r"['\"].*OR.*['\"].*=.*['\"]",
        r"admin['\"]?\s*--",
        r"1\s*=\s*1",
        r"['\"].*OR.*1\s*=\s*1"
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False

def validate_password(password: str) -> str:
    """Validate password strength"""
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    if len(password) > 100:
        raise HTTPException(status_code=400, detail="Password too long")
    
    return password

def sanitize_login_input(email: str, password: str) -> tuple[str, str]:
    """Sanitize and validate login inputs"""
    
    # Check for SQL injection attempts
    if detect_sql_injection(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if detect_sql_injection(password):
        raise HTTPException(status_code=400, detail="Invalid password format")
    
    # Validate email
    email = validate_email(email)
    
    # Validate password (basic check, don't escape password)
    password = validate_password(password)
    
    return email, password