from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.utils.dependencies import get_current_user
from app.database import get_db
from app.models.contract import Contract
from app.models.review import Review
from app.models.activity import Activity

router = APIRouter()

# -----------------------------
# User Info
# -----------------------------
@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "plan": "Pro"
    }


# -----------------------------
# Dashboard Stats
# -----------------------------
@router.get("/stats")
async def stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result_contracts = await db.execute(
        select(func.count()).select_from(Contract).where(Contract.user_id == current_user.id)
    )
    contracts_count = result_contracts.scalar() or 0

    result_reviews = await db.execute(
        select(func.count()).select_from(Review).where(Review.user_id == current_user.id)
    )
    reviews_count = result_reviews.scalar() or 0

    result_blockchain = await db.execute(
        select(func.count()).select_from(Activity).where(
            Activity.user_id == current_user.id,
            Activity.event_type.in_(["blockchain_embed", "blockchain_verify"])
        )
    )
    blockchain_count = result_blockchain.scalar() or 0

    return {
        "contracts": contracts_count,
        "reviews": reviews_count,
        "blockchain": blockchain_count
    }


# -----------------------------
# Recent Activity
# -----------------------------
@router.get("/activity")
async def activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Activity)
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .limit(10)
    )

    activities = result.scalars().all()

    return [
        {
            "event_type": a.event_type,
            "message": a.message,
            "time": a.created_at.isoformat()
        }
        for a in activities
    ]
