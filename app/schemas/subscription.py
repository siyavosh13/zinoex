from pydantic import BaseModel
from typing import Optional, Any
from app.models.subscription import BillingCycle, PaymentStatus

class PlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    price_lifetime: Optional[float]
    features: dict
    is_featured: bool

    class Config:
        from_attributes = True

class PlanCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    price_lifetime: Optional[float] = None
    features: dict = {}
    is_active: bool = True
    is_featured: bool = False

class PlanUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    price_lifetime: Optional[float] = None
    features: Optional[dict] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class SubscribeRequest(BaseModel):
    plan_id: int
    billing_cycle: BillingCycle
    payment_gateway: Optional[str] = "stripe"

class SubscriptionResponse(BaseModel):
    id: int
    plan_id: int
    billing_cycle: str
    status: str
    amount: float
    currency: str
    starts_at: Optional[Any]
    expires_at: Optional[Any]
    activated_by_admin: bool
    created_at: Any

    class Config:
        from_attributes = True

class AdminActivatePlanRequest(BaseModel):
    user_id: int
    plan_id: int
    billing_cycle: BillingCycle
    admin_note: Optional[str] = None
