import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.subscription import Plan, Subscription, PaymentStatus
from app.models.user import User
from app.schemas.subscription import (
    PlanResponse, SubscribeRequest,
    SubscriptionResponse
)
from app.services.subscription_service import activate_subscription
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

# ─── Public ──────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    """Get all available plans - public endpoint"""
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.price_monthly)
    )
    return result.scalars().all()

@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

# ─── Authenticated ────────────────────────────────────────

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    data: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate subscription - integrates with payment gateway.
    Currently creates a PENDING subscription and returns payment intent.
    """
    logger.info(
        f"Subscribe request | user_id={current_user.id} "
        f"| plan_id={data.plan_id} | cycle={data.billing_cycle}"
    )

    result = await db.execute(select(Plan).where(Plan.id == data.plan_id))
    plan = result.scalar_one_or_none()
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")

    # For FREE plan - activate immediately without payment
    if plan.name == "free":
        subscription = await activate_subscription(
            db=db,
            user=current_user,
            plan=plan,
            billing_cycle=data.billing_cycle,
            gateway="free"
        )
        return subscription

    # For paid plans - create payment intent (Stripe example)
    # TODO: Integrate Stripe / PayPal here
    # payment_intent = await stripe_service.create_intent(amount, currency)
    
    # For now - return pending subscription
    from app.services.subscription_service import get_plan_price
    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        billing_cycle=data.billing_cycle,
        status=PaymentStatus.PENDING,
        amount=get_plan_price(plan, data.billing_cycle),
        payment_gateway=data.payment_gateway,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    logger.info(f"Pending subscription created | subscription_id={subscription.id}")

    return subscription


@router.post("/confirm/{subscription_id}", response_model=SubscriptionResponse)
async def confirm_payment(
    subscription_id: int,
    payment_intent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm payment after gateway callback"""
    logger.info(
        f"Payment confirmation | subscription_id={subscription_id} "
        f"| payment_intent={payment_intent_id} | user_id={current_user.id}"
    )

    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == current_user.id
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.status == PaymentStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Subscription already activated")

    # TODO: Verify payment with gateway
    # verified = await stripe_service.verify_intent(payment_intent_id)

    result_plan = await db.execute(select(Plan).where(Plan.id == subscription.plan_id))
    plan = result_plan.scalar_one_or_none()

    activated = await activate_subscription(
        db=db,
        user=current_user,
        plan=plan,
        billing_cycle=subscription.billing_cycle,
        payment_intent_id=payment_intent_id,
        gateway=subscription.payment_gateway or "stripe"
    )

    return activated


@router.get("/my", response_model=list[SubscriptionResponse])
async def my_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription history"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().all()


@router.get("/my/active", response_model=SubscriptionResponse)
async def active_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's current active subscription"""
    from datetime import datetime
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == PaymentStatus.SUCCESS,
            Subscription.expires_at > datetime.utcnow()
        ).order_by(Subscription.expires_at.desc())
    )
    subscription = result.scalars().first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    return subscription


@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an active subscription"""
    from datetime import datetime
    from app.models.user import SubscriptionStatus

    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == current_user.id
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.status = PaymentStatus.REFUNDED
    subscription.cancelled_at = datetime.utcnow()
    current_user.subscription_status = SubscriptionStatus.CANCELLED

    await db.commit()
    logger.info(f"Subscription cancelled | subscription_id={subscription_id} | user_id={current_user.id}")

    return {"message": "Subscription cancelled successfully"}
