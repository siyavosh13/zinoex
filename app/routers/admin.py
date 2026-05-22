import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import List, Optional
import shutil
import os

from app.database import get_db
from app.models.user import User
from app.models.admin import SiteModule, SiteIndex, ActivityLog, MediaFile
from app.models.subscription import Plan, Subscription
from app.schemas.admin import (
    ModuleCreate, ModuleUpdate,
    IndexUpdate, BatchContentUpdate
)
from app.schemas.subscription import (
    PlanCreate, PlanUpdate, AdminActivatePlanRequest
)
from app.services.subscription_service import activate_subscription
from app.utils.dependencies import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────
#   USER MANAGEMENT
# ──────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/users/{user_id}/usage")
async def get_user_usage(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Monthly usage for dashboard user table."""
    month_start = datetime.utcnow().replace(day=1)
    result = await db.execute(
        select(
            func.count(ActivityLog.id).label("total_actions"),
            func.sum(
                func.case((ActivityLog.module == "Contract", 1), else_=0)
            ).label("contracts"),
            func.sum(
                func.case((ActivityLog.module == "RiskCheck", 1), else_=0)
            ).label("risk_checks"),
        )
        .where(ActivityLog.user_id == user_id)
        .where(ActivityLog.timestamp >= month_start)
    )
    row = result.first()
    return {
        "contracts": row.contracts or 0,
        "risk_checks": row.risk_checks or 0,
        "total": row.total_actions or 0
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    await db.delete(user)
    await db.commit()
    logger.info(f"User deleted | {user_id} by admin={admin.id}")
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if user.is_admin:
        return {"message": "User already admin"}

    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return {"message": "User promoted", "user_id": user.id}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    await db.commit()
    return {"message": "User suspended"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = True
    await db.commit()
    return {"message": "User activated"}


# ──────────────────────────────────────────────────────────────
#   SUBSCRIPTIONS
# ──────────────────────────────────────────────────────────────

@router.post("/subscriptions/activate")
async def admin_activate_plan(
    data: AdminActivatePlanRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result_user = await db.execute(select(User).where(User.id == data.user_id))
    user = result_user.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    result_plan = await db.execute(select(Plan).where(Plan.id == data.plan_id))
    plan = result_plan.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    subscription = await activate_subscription(
        db=db,
        user=user,
        plan=plan,
        billing_cycle=data.billing_cycle,
        activated_by_admin=True,
        admin_note=data.admin_note or f"Manual by admin {admin.id}"
    )
    return {"message": "Activated", "subscription": subscription}


@router.post("/subscriptions/{sub_id}/cancel")
async def cancel_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(Subscription).where(Subscription.id == sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    sub.is_active = False
    await db.commit()
    return {"message": "Subscription canceled"}


@router.get("/subscriptions")
async def list_all_subscriptions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(Subscription).offset(skip).limit(limit).order_by(desc(Subscription.created_at))
    )
    return result.scalars().all()


# ──────────────────────────────────────────────────────────────
#   PLAN MANAGEMENT
# ──────────────────────────────────────────────────────────────

@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    result = await db.execute(select(Plan))
    return result.scalars().all()


@router.post("/plans")
async def create_plan(
    data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    plan = Plan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    for k, v in data.model_dump(exclude_none=True).items():
        setattr(plan, k, v)

    await db.commit()
    return plan


@router.post("/plans/{plan_id}/enable")
async def enable_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    plan.is_active = True
    await db.commit()
    return {"message": "Enabled"}


@router.post("/plans/{plan_id}/disable")
async def disable_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    plan.is_active = False
    await db.commit()
    return {"message": "Disabled"}


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    await db.delete(plan)
    await db.commit()
    return {"message": "Plan deleted"}


# ──────────────────────────────────────────────────────────────
#   SITE MODULES
# ──────────────────────────────────────────────────────────────

@router.get("/modules")
async def list_modules(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    result = await db.execute(select(SiteModule).order_by(SiteModule.order))
    return result.scalars().all()


@router.post("/modules")
async def create_module(
    data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    module = SiteModule(**data.model_dump())
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


@router.put("/modules/{module_id}")
async def update_module(
    module_id: int,
    data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(SiteModule).where(SiteModule.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(404, "Module not found")

    for k, v in data.model_dump(exclude_none=True).items():
        setattr(module, k, v)

    await db.commit()
    return module


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(SiteModule).where(SiteModule.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(404, "Module not found")

    await db.delete(module)
    await db.commit()
    return {"message": "Module deleted"}


# ──────────────────────────────────────────────────────────────
#   INDEX / SITE CONTENT
# ──────────────────────────────────────────────────────────────

@router.get("/index")
async def list_index(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin)):
    result = await db.execute(select(SiteIndex))
    return result.scalars().all()


@router.put("/index")
async def upsert_index(
    data: IndexUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(SiteIndex).where(SiteIndex.key == data.key))
    item = result.scalar_one_or_none()

    if item:
        item.value = data.value
        item.description = data.description
    else:
        item = SiteIndex(**data.model_dump())
        db.add(item)

    await db.commit()
    return item


@router.put("/content/batch")
async def batch_content_update(
    data: BatchContentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """Save multiple keys at once for 'Save All Changes' button"""
    for key, value in data.dict().items():
        result = await db.execute(select(SiteIndex).where(SiteIndex.key == key))
        item = result.scalar_one_or_none()

        if item:
            item.value = value
        else:
            db.add(SiteIndex(key=key, value=value))

    await db.commit()
    return {"message": "Content updated"}


@router.delete("/index/{key}")
async def delete_index(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(SiteIndex).where(SiteIndex.key == key))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Not found")

    await db.delete(item)
    await db.commit()
    return {"message": "Index item deleted"}


# ──────────────────────────────────────────────────────────────
#   ACTIVITY LOGS
# ──────────────────────────────────────────────────────────────

@router.get("/activity")
async def get_activity_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(ActivityLog)
        .order_by(desc(ActivityLog.timestamp))
        .limit(limit)
    )
    return result.scalars().all()


@router.delete("/activity")
async def clear_activity_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    await db.execute("DELETE FROM activity_logs")
    await db.commit()
    return {"message": "Activity logs cleared"}


# ──────────────────────────────────────────────────────────────
#   FILE MANAGER
# ──────────────────────────────────────────────────────────────

@router.post("/files")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    file_path = os.path.join(MEDIA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    media = MediaFile(filename=file.filename, path=file_path)
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


@router.get("/files")
async def list_files(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(MediaFile))
    return result.scalars().all()


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result = await db.execute(select(MediaFile).where(MediaFile.id == file_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(404, "File not found")

    try:
        os.remove(media.path)
    except:
        pass

    await db.delete(media)
    await db.commit()
    return {"message": "File deleted"}


# ──────────────────────────────────────────────────────────────
#   DASHBOARD STATS
# ──────────────────────────────────────────────────────────────

@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    result_users = await db.execute(select(func.count(User.id)))
    total_users = result_users.scalar()

    result_active_subs = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.is_active == True)
    )
    active_subs = result_active_subs.scalar()

    month_start = datetime.utcnow().replace(day=1)
    result_usage = await db.execute(
        select(
            func.count(ActivityLog.id),
            func.sum(func.case((ActivityLog.module == "Contract", 1), else_=0)),
            func.sum(func.case((ActivityLog.module == "RiskCheck", 1), else_=0)),
        ).where(ActivityLog.timestamp >= month_start)
    )
    usage = result_usage.first()

    recent_activity_result = await db.execute(
        select(ActivityLog).order_by(desc(ActivityLog.timestamp)).limit(10)
    )

    return {
        "total_users": total_users,
        "active_subscriptions": active_subs,
        "monthly_usage": {
            "contracts": usage[1] or 0,
            "risk_checks": usage[2] or 0,
            "total": usage[0] or 0,
        },
        "recent_activity": recent_activity_result.scalars().all()
    }
