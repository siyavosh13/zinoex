import asyncio
import sys
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
import app.models  # این خط باعث لود همه مدل‌ها از __init__ می‌شود


async def make_admin(email: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()

        if not user:
            print(f"[!] User with email '{email}' not found.")
            return

        user.is_admin = True
        user.is_active = True

        await session.commit()
        print(f"[OK] User '{email}' is now ADMIN.")


if __name__ == "__main__":
    # اگر ایمیل را از خط فرمان دادی، از همان استفاده کن
    if len(sys.argv) > 1:
        target_email = sys.argv[1]
    else:
        # در غیر این صورت، این ایمیل را به صورت ثابت تنظیم کن
        target_email = "siyaavash67@gmail.com"

    asyncio.run(make_admin(target_email))
