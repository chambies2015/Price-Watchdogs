from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.user import UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.auth import get_current_user
from app.middleware.rate_limit import limiter
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=uuid.uuid4(),
        email=user_data.email,
        password_hash=hashed_password
    )
    
    import os
    admin_email = os.getenv('ADMIN_EMAIL')
    if admin_email and user_data.email == admin_email:
        new_user.is_admin = True
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    import os
    admin_email = os.getenv('ADMIN_EMAIL')
    if admin_email and user.email == admin_email and not user.is_admin:
        user.is_admin = True
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/debug/admin-status")
async def debug_admin_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import os
    result = await db.execute(select(User).where(User.id == current_user.id))
    fresh_user = result.scalar_one_or_none()
    
    return {
        "email": current_user.email,
        "is_admin_from_token": current_user.is_admin,
        "is_admin_from_db": fresh_user.is_admin if fresh_user else None,
        "admin_email_env": os.getenv('ADMIN_EMAIL'),
        "match": current_user.email == os.getenv('ADMIN_EMAIL')
    }
