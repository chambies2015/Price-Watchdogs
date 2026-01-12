import asyncio
import sys
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


async def set_admin_status(email: str, is_admin: bool = True):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        user.is_admin = is_admin
        await db.commit()
        
        status = "admin" if is_admin else "regular user"
        print(f"✅ User '{email}' (ID: {user.id}) is now an {status}")
        return True


async def main():
    if len(sys.argv) < 2:
        print("Usage: python set_admin.py <email>")
        print("Example: python set_admin.py user@example.com")
        return
    
    email = sys.argv[1]
    await set_admin_status(email, is_admin=True)


if __name__ == "__main__":
    asyncio.run(main())
