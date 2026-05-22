from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.security import verify_password, hash_password


router = APIRouter(prefix="/profile", tags=["Profile"])


# ============================
#   SCHEMAS
# ============================

class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None
    company: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============================
#   GET PROFILE
# ============================

@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # Load profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    # If not exists → create empty profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "plan": current_user.plan,
        "plan_expires_at": current_user.plan_expires_at,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,

        "profile": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "username": profile.username,
            "phone": profile.phone,
            "company": profile.company,
            "avatar_url": profile.avatar_url,
        }
    }


# ============================
#   UPDATE PROFILE
# ============================

@router.put("/update")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)

    profile.first_name = data.first_name
    profile.last_name = data.last_name
    profile.username = data.username
    profile.phone = data.phone
    profile.company = data.company

    db.add(profile)
    await db.commit()

    return {"message": "Profile updated successfully"}


# ============================
#   CHANGE PASSWORD
# ============================

@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")

    current_user.hashed_password = get_password_hash(data.new_password)

    db.add(current_user)
    await db.commit()

    return {"message": "Password changed successfully"}


# ============================
#   DASHBOARD (نسخه قبلی تو)
# ============================

@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "email": current_user.email,
            "plan": current_user.plan,
        },
        "stats": {
            "contracts_generated": 0,
            "contracts_verified": 0,
        }
    }
