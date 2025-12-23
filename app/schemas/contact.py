from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

class ContactCreate(BaseModel):
    """
    Schema for creating a new contact inquiry
    Matches your frontend payload exactly
    """
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    phone: str = Field(..., description="Phone number")
    eventDate: str = Field(..., alias="eventDate", description="Event date in DD-MM-YYYY format")
    message: Optional[str] = Field(None, max_length=2000, description="Customer message")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name contains only letters and spaces"""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Name must contain only letters and spaces")
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate Indian phone number format"""
        # Remove spaces, hyphens, and plus signs
        cleaned = re.sub(r'[\s\-\+]', '', v)
        
        # Check if it's a valid Indian number (10 digits, optionally with country code)
        if re.match(r'^91\d{10}$', cleaned):  # With country code
            return f"+91 {cleaned[2:7]} {cleaned[7:]}"
        elif re.match(r'^\d{10}$', cleaned):  # Without country code
            return f"+91 {cleaned[:5]} {cleaned[5:]}"
        else:
            raise ValueError("Invalid phone number. Must be 10 digits (optionally with +91)")
    
    @validator('eventDate')
    def validate_event_date(cls, v):
        """Validate date format DD-MM-YYYY"""
        if not re.match(r'^\d{2}-\d{2}-\d{4}$', v):
            raise ValueError("Event date must be in DD-MM-YYYY format (e.g., 20-03-2025)")
        
        # Additional validation: Check if date is valid
        try:
            day, month, year = map(int, v.split('-'))
            if not (1 <= day <= 31 and 1 <= month <= 12 and year >= 2024):
                raise ValueError
        except:
            raise ValueError("Invalid date. Please check day, month, and year values")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "phone": "+91 9876543210",
                "eventDate": "20-03-2025",
                "message": "We are looking for a pre-wedding shoot in Jaipur. Please share details."
            }
        }


class ContactResponse(BaseModel):
    """
    Schema for contact inquiry response
    """
    id: int
    name: str
    email: str
    phone: str
    event_date: str
    message: Optional[str]
    is_read: bool
    is_responded: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Rahul Sharma",
                "email": "rahul@example.com",
                "phone": "+91 98765 43210",
                "event_date": "20-03-2025",
                "message": "We are looking for a pre-wedding shoot in Jaipur.",
                "is_read": False,
                "is_responded": False,
                "created_at": "2025-01-15T10:30:00"
            }
        }


class ContactListResponse(BaseModel):
    """
    Schema for listing contacts (admin only)
    """
    contacts: list[ContactResponse]
    total: int
    unread_count: int
    
    
class ContactUpdateStatus(BaseModel):
    """
    Schema for admin to update contact status
    """
    is_read: Optional[bool] = None
    is_responded: Optional[bool] = None
    admin_notes: Optional[str] = Field(None, max_length=1000)