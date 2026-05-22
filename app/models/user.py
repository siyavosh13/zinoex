from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class PlanType(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    verification_code = Column(String, nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)

    plan = Column(Enum(PlanType), default=PlanType.FREE)
    plan_expires_at = Column(DateTime, nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # =========================
    # Relationships
    # =========================

    # Contracts
    contracts = relationship(
        "Contract",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Reviews
    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # User Profile (One-to-One)
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Activities
    activities = relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Subscriptions
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
