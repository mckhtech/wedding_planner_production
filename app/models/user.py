from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=True)
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    google_id = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # ============================================
    # CREDIT SYSTEM (KEPT FOR HISTORICAL DATA)
    # ============================================
    free_credits_remaining = Column(Integer, default=2)  # Kept for backward compatibility
    
    # Subscription info
    is_subscribed = Column(Boolean, default=False)
    subscription_expiry = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generations = relationship("Generation", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payment_tokens = relationship("PaymentToken", back_populates="user", cascade="all, delete-orphan")
    
    # ============================================
    # HELPER METHODS - UPDATED FOR UNLIMITED FREE GENERATIONS
    # ============================================
    
    @property
    def credits_remaining(self):
        """Backward compatibility - returns free credits (historical only)"""
        return self.free_credits_remaining
    
    def can_generate_with_free_template(self) -> bool:
        """
        Check if user can generate with a FREE template
        
        NEW BEHAVIOR: Always returns True (unlimited generations)
        """
        return True  # ✅ UNLIMITED FREE GENERATIONS
        
        # ============================================
        # OLD LOGIC (COMMENTED OUT FOR REFERENCE)
        # ============================================
        # """
        # Check if user can generate with a FREE template
        # Requires: At least 1 free credit remaining
        # """
        # return self.free_credits_remaining > 0
    
    def deduct_free_credit(self) -> bool:
        """
        Deduct one free credit from user
        
        NEW BEHAVIOR: Always returns True without deducting anything
        (Keeps the method for backward compatibility but doesn't deduct credits)
        """
        return True  # ✅ NO DEDUCTION, UNLIMITED GENERATIONS
        
        # ============================================
        # OLD LOGIC (COMMENTED OUT FOR REFERENCE)
        # ============================================
        # """
        # Deduct one free credit from user
        # Returns True if successful, False if no credits remaining
        # """
        # if self.free_credits_remaining <= 0:
        #     return False
        # self.free_credits_remaining -= 1
        # return True
    
    def can_generate_with_paid_template(self, template_id: int) -> bool:
        """
        Check if user has an available paid token for specific paid template
        Returns True if user has a token with uses_remaining > 0
        
        NO CHANGES - Paid templates still require tokens
        """
        from app.models.payment_token import PaymentToken
        
        available_token = next(
            (token for token in self.payment_tokens 
             if token.template_id == template_id 
             and token.can_be_used()),
            None
        )
        return available_token is not None
    
    def get_unused_token_for_template(self, template_id: int):
        """
        Get the first available paid token for a specific template
        Returns tokens with uses_remaining > 0
        
        NO CHANGES - Paid templates still require tokens
        """
        from app.models.payment_token import PaymentToken
        
        return next(
            (token for token in self.payment_tokens 
             if token.template_id == template_id 
             and token.can_be_used()),
            None
        )
    
    def get_token_usage_for_template(self, template_id: int) -> dict:
        """
        Get token usage summary for a template
        Returns dict with total_uses, uses_remaining, and tokens info
        
        NO CHANGES - For paid templates only
        """
        from app.models.payment_token import PaymentToken, PaymentStatus
        
        tokens = [
            token for token in self.payment_tokens 
            if token.template_id == template_id 
            and token.payment_status == PaymentStatus.COMPLETED
        ]
        
        total_uses_purchased = sum(token.uses_total for token in tokens)
        total_uses_remaining = sum(token.uses_remaining for token in tokens)
        total_uses_consumed = total_uses_purchased - total_uses_remaining
        
        return {
            "total_tokens": len(tokens),
            "total_uses_purchased": total_uses_purchased,
            "uses_remaining": total_uses_remaining,
            "uses_consumed": total_uses_consumed,
            "available_tokens": [
                {
                    "token_id": token.id,
                    "uses_remaining": token.uses_remaining,
                    "uses_total": token.uses_total
                }
                for token in tokens if token.can_be_used()
            ]
        }