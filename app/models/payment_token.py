from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class TokenStatus(str, enum.Enum):
    UNUSED = "unused"
    USED = "used"
    REFUNDED = "refunded"
    EXPIRED = "expired"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    
class PaymentToken(Base):
    __tablename__ = "payment_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    payment_id = Column(String, unique=True, nullable=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="INR")
    status = Column(Enum(TokenStatus), default=TokenStatus.UNUSED)
    
    # ============================================
    # NEW: Multi-use token system
    # ============================================
    uses_total = Column(Integer, default=2, nullable=False)  # Total uses allowed
    uses_remaining = Column(Integer, default=2, nullable=False)  # Uses left
    
    used_at = Column(DateTime, nullable=True)  # First use timestamp
    last_used_at = Column(DateTime, nullable=True)  # Most recent use
    refund_id = Column(String, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    refund_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)    
    
    user = relationship("User", back_populates="payment_tokens")
    template = relationship("Template", back_populates="payment_tokens")
    generations = relationship("Generation", back_populates="payment_token")

    # ============================================
    # UPDATED METHODS
    # ============================================
    
    def can_be_used(self) -> bool:
        """Check if token still has uses remaining"""
        return (
            self.payment_status == PaymentStatus.COMPLETED and
            self.status != TokenStatus.REFUNDED and
            self.status != TokenStatus.EXPIRED and
            self.uses_remaining > 0
        )
    
    def use_token(self):
        """
        Deduct one use from the token
        Automatically marks as USED when uses_remaining reaches 0
        """
        if self.uses_remaining <= 0:
            raise ValueError("No uses remaining on this token")
        
        # First use
        if self.used_at is None:
            self.used_at = datetime.utcnow()
        
        # Deduct use
        self.uses_remaining -= 1
        self.last_used_at = datetime.utcnow()
        
        # Mark as fully used if no uses left
        if self.uses_remaining == 0:
            self.status = TokenStatus.USED
    
    def mark_as_used(self, generation_id: int = None):
        """
        Legacy method - now calls use_token()
        Kept for backward compatibility
        """
        self.use_token()

    def mark_as_refunded(self, refund_id: str, reason: str):
        """Mark token as refunded."""
        self.status = TokenStatus.REFUNDED
        self.payment_status = PaymentStatus.REFUNDED
        self.refund_id = refund_id
        self.refund_reason = reason
        self.refunded_at = datetime.utcnow()
    
    @property
    def is_available(self) -> bool:
        """Check if token is available for use"""
        return self.can_be_used()
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage (0-100)"""
        if self.uses_total == 0:
            return 100.0
        used = self.uses_total - self.uses_remaining
        return (used / self.uses_total) * 100