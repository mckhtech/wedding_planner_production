from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserGoogleAuth(BaseModel):
    google_token: str

class UserResponse(UserBase):
    """
    User response schema - UPDATED to remove credit display
    
    ✨ Free templates now have unlimited generations!
    Credits field removed from API response.
    """
    id: int
    is_active: bool
    is_admin: bool
    is_subscribed: bool
    profile_picture: Optional[str] = None
    created_at: datetime
    
    # ============================================
    # REMOVED: credits_remaining field
    # ============================================
    # credits_remaining: int  # ❌ Removed - no longer relevant with unlimited free generations
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class CreditsResponse(BaseModel):
    """
    DEPRECATED: This endpoint is no longer needed with unlimited free generations
    
    Consider removing the /credits endpoint entirely, or update it to only show
    subscription status and paid template access.
    """
    # ============================================
    # OPTION 1: Remove this schema entirely
    # ============================================
    # Delete this class and remove the /credits endpoint
    
    # ============================================
    # OPTION 2: Update to show subscription info only
    # ============================================
    is_subscribed: bool
    subscription_expiry: Optional[datetime] = None
    
    # Remove these fields:
    # credits_remaining: int  # ❌ No longer relevant
    # can_generate: bool      # ❌ Always True for free templates now


# ============================================
# NEW: Subscription-focused response (optional)
# ============================================
class UserAccessResponse(BaseModel):
    """
    NEW: Replace CreditsResponse with subscription-focused response
    
    Shows what the user has access to without mentioning credits.
    """
    is_subscribed: bool
    subscription_expiry: Optional[datetime] = None
    has_watermark_free_generations: bool  # True if not subscribed
    
    # For paid templates
    paid_templates_access: dict  # {"template_id": {"uses_remaining": X, "uses_total": Y}}
    
    class Config:
        from_attributes = True


# ============================================
# OLD SCHEMAS (COMMENTED FOR REFERENCE)
# ============================================
# class CreditsResponse(BaseModel):
#     """OLD VERSION - Had credit limits"""
#     credits_remaining: int
#     is_subscribed: bool
#     can_generate: bool