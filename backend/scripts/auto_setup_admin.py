import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


async def setup_admin():
    admin_email = os.getenv('ADMIN_EMAIL')
    
    if not admin_email:
        print("⚠️  No ADMIN_EMAIL environment variable set. Skipping admin setup.")
        return False
    
    print(f"🔍 Checking for admin setup: {admin_email}")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == admin_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"⚠️  User with email '{admin_email}' not found. Admin will be set when user registers.")
            return False
        
        if user.is_admin:
            print(f"✅ User '{admin_email}' is already an admin. No changes needed.")
            return True
        
        user.is_admin = True
        await db.commit()
        print(f"✅ User '{admin_email}' (ID: {user.id}) has been set as admin!")
        return True


async def main():
    try:
        await setup_admin()
    except Exception as e:
        print(f"❌ Error during admin setup: {e}")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
