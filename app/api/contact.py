from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact import (
    ContactCreate, 
    ContactResponse, 
    ContactListResponse,
    ContactUpdateStatus
)
from app.utils.dependencies import get_current_user
import logging

router = APIRouter(prefix="/api/contact", tags=["Contact"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new contact inquiry
    
    PUBLIC ENDPOINT - No authentication required
    This allows visitors to submit inquiries from your landing page.
    """
    try:
        # Create contact record
        contact = Contact(
            name=contact_data.name,
            email=contact_data.email,
            phone=contact_data.phone,
            event_date=contact_data.eventDate,  # Note: using alias
            message=contact_data.message,
            is_read=False,
            is_responded=False
        )
        
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        logger.info(f"✅ New contact inquiry created: {contact.id} - {contact.name} ({contact.email})")
        
        # TODO: Send email notification to admin
        # send_contact_notification_email(contact)
        
        return contact
        
    except Exception as e:
        logger.error(f"❌ Contact creation failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit inquiry. Please try again."
        )


@router.get("/", response_model=ContactListResponse)
async def get_all_contacts(
    skip: int = 0,
    limit: int = 50,
    is_read: Optional[bool] = None,
    is_responded: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all contact inquiries (Admin only)
    
    Query parameters:
    - skip: Pagination offset
    - limit: Number of records to return
    - is_read: Filter by read status
    - is_responded: Filter by responded status
    """
    # Check admin access
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Build query
    query = db.query(Contact)
    
    # Apply filters
    if is_read is not None:
        query = query.filter(Contact.is_read == is_read)
    if is_responded is not None:
        query = query.filter(Contact.is_responded == is_responded)
    
    # Get total count and unread count
    total = query.count()
    unread_count = db.query(Contact).filter(Contact.is_read == False).count()
    
    # Get paginated results
    contacts = query.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "contacts": contacts,
        "total": total,
        "unread_count": unread_count
    }


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific contact inquiry (Admin only)
    
    Automatically marks the contact as read when viewed.
    """
    # Check admin access
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact inquiry not found"
        )
    
    # Mark as read if not already
    if not contact.is_read:
        contact.is_read = True
        db.commit()
        db.refresh(contact)
        logger.info(f"📧 Contact {contact_id} marked as read by admin {current_user.id}")
    
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact_status(
    contact_id: int,
    status_update: ContactUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update contact inquiry status (Admin only)
    
    Allows admin to mark as read/responded and add notes.
    """
    # Check admin access
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact inquiry not found"
        )
    
    # Update fields
    if status_update.is_read is not None:
        contact.is_read = status_update.is_read
    if status_update.is_responded is not None:
        contact.is_responded = status_update.is_responded
    if status_update.admin_notes is not None:
        contact.admin_notes = status_update.admin_notes
    
    db.commit()
    db.refresh(contact)
    
    logger.info(f"✏️ Contact {contact_id} updated by admin {current_user.id}")
    
    return contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a contact inquiry (Admin only)
    
    Use with caution - this permanently deletes the inquiry.
    """
    # Check admin access
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact inquiry not found"
        )
    
    db.delete(contact)
    db.commit()
    
    logger.info(f"🗑️ Contact {contact_id} deleted by admin {current_user.id}")
    
    return {"message": "Contact inquiry deleted successfully"}


@router.get("/stats/summary")
async def get_contact_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get contact inquiry statistics (Admin only)
    
    Returns summary stats for admin dashboard.
    """
    # Check admin access
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    total_inquiries = db.query(Contact).count()
    unread_inquiries = db.query(Contact).filter(Contact.is_read == False).count()
    responded_inquiries = db.query(Contact).filter(Contact.is_responded == True).count()
    pending_inquiries = db.query(Contact).filter(Contact.is_responded == False).count()
    
    # Get recent inquiries (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_inquiries = db.query(Contact).filter(
        Contact.created_at >= seven_days_ago
    ).count()
    
    return {
        "total_inquiries": total_inquiries,
        "unread_inquiries": unread_inquiries,
        "responded_inquiries": responded_inquiries,
        "pending_inquiries": pending_inquiries,
        "recent_inquiries_7_days": recent_inquiries
    }