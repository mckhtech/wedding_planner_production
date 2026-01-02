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
    User response schema - RESTORED credit display
    
    ✅ Shows free_credits_remaining (5 for new users)
    """
    id: int
    is_active: bool
    is_admin: bool
    is_subscribed: bool
    profile_picture: Optional[str] = None
    created_at: datetime
    
    # ============================================
    # RESTORED: credits_remaining field
    # ============================================
    free_credits_remaining: int  # ✅ RESTORED: Shows remaining free credits
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class CreditsResponse(BaseModel):
    """
    Credit and access information for user
    
    ✅ RESTORED: Shows credit balance and subscription status
    """
    user_id: int
    email: str
    free_credits_remaining: int
    is_subscribed: bool
    can_generate_free: bool
    message: str
    
    class Config:
        from_attributes = True