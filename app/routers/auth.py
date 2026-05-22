import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.user import User, SubscriptionStatus
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest,
    VerifyEmailRequest, ResendCodeRequest,
    TokenResponse, UserResponse
)

from app.services.email_service import generate_verification_code, send_verification_email
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])


# ========================================================
# Register
# ========================================================

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Register attempt for email: {data.email}")

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    code = generate_verification_code()
    expires = datetime.utcnow() + timedelta(minutes=10)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        verification_code=code,
        verification_code_expires=expires,
        is_verified=False,
        is_active=False,
        plan="free",
        subscription_status=SubscriptionStatus.PENDING
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(_send_email_safe, data.email, code)

    return user


async def _send_email_safe(email: str, code: str):
    try:
        await send_verification_email(email, code)
    except Exception as e:
        logger.warning(f"Email send failed: {e}")


# ========================================================
# Verify Email
# ========================================================

@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Email verification for: {data.email}")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    if user.verification_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if datetime.utcnow() > user.verification_code_expires:
        raise HTTPException(status_code=400, detail="Verification code has expired")

    user.is_verified = True
    user.is_active = True
    user.verification_code = None
    user.verification_code_expires = None

    await db.commit()

    return {"message": "Email verified successfully"}


# ========================================================
# Login
# ========================================================

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login attempt for: {data.email}")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    token = create_access_token({"sub": str(user.id), "email": user.email})

    return {"access_token": token}


# ========================================================
# Get Current User (Protected)
# ========================================================

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "plan": user.plan,
        "subscription_status": user.subscription_status
    }


# ========================================================
# Resend Code
# ========================================================

@router.post("/resend-code")
async def resend_code(data: ResendCodeRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Resend code for: {data.email}")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)

    await db.commit()
    await send_verification_email(data.email, code)

    return {"message": "Verification code resent successfully"}
