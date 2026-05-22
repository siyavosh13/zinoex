from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    price_lifetime = Column(Float, nullable=True)

    features = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    billing_cycle = Column(Enum(BillingCycle), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")

    # Payment gateway info
    payment_gateway = Column(String, nullable=True)
    payment_intent_id = Column(String, nullable=True)
    payment_metadata = Column(JSON, default={})

    # Dates
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Manual activation by admin
    activated_by_admin = Column(Boolean, default=False)
    admin_note = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # relationships
    plan = relationship("Plan", back_populates="subscriptions")

    # ✅ اضافه شد برای حل خطا
    user = relationship("User", back_populates="subscriptions")
