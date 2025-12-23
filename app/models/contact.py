from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.database import Base

class Contact(Base):
    """
    Contact/Inquiry model for pre-wedding shoot inquiries
    
    Stores customer contact information and event details
    """
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contact Information
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    
    # Event Details
    event_date = Column(String, nullable=True)  # Stored as string (DD-MM-YYYY format)
    message = Column(Text, nullable=True)
    
    # Status Tracking
    is_read = Column(Boolean, default=False)
    is_responded = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional: Admin notes
    admin_notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', email='{self.email}')>"