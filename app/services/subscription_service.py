import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.subscription import Subscription, Plan, BillingCycle, PaymentStatus
from app.models.user import User, PlanType, SubscriptionStatus

logger = logging.getLogger(__name__)

def calculate_expiry(billing_cycle: BillingCycle) -> datetime:
    now = datetime.utcnow()
    if billing_cycle == BillingCycle.MONTHLY:
        return now + timedelta(days=30)
    elif billing_cycle == BillingCycle.YEARLY:
        return now + timedelta(days=365)
    elif billing_cycle == BillingCycle.LIFETIME:
        return now + timedelta(days=36500)     # 100 years
    return now + timedelta(days=30)

def get_plan_price(plan: Plan, billing_cycle: BillingCycle) -> float:
    if billing_cycle == BillingCycle.MONTHLY:
        return plan.price_monthly
    elif billing_cycle == BillingCycle.YEARLY:
        return plan.price_yearly
    elif billing_cycle == BillingCycle.LIFETIME:
        return plan.price_lifetime or plan.price_monthly * 12
    return plan.price_monthly

async def activate_subscription(
    db: AsyncSession,
    user: User,
    plan: Plan,
    billing_cycle: BillingCycle,
    payment_intent_id: str = None,
    gateway: str = "stripe",
    activated_by_admin: bool = False,
    admin_note: str = None
) -> Subscription:
    
    now = datetime.utcnow()
    expires_at = calculate_expiry(billing_cycle)
    amount = get_plan_price(plan, billing_cycle)

    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        billing_cycle=billing_cycle,
        status=PaymentStatus.SUCCESS,
        amount=amount,
        payment_gateway=gateway if not activated_by_admin else "manual",
        payment_intent_id=payment_intent_id,
        starts_at=now,
        expires_at=expires_at,
        activated_by_admin=activated_by_admin,
        admin_note=admin_note
    )

    db.add(subscription)

    # Update user plan
    user.plan = PlanType(plan.name)
    user.plan_expires_at = expires_at
    user.subscription_status = SubscriptionStatus.ACTIVE

    await db.commit()
    await db.refresh(subscription)

    logger.info(
        f"Subscription activated | user_id={user.id} | plan={plan.name} "
        f"| cycle={billing_cycle} | expires={expires_at} "
        f"| admin={activated_by_admin}"
    )

    return subscription
