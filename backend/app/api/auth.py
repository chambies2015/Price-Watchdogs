from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from app.schemas.user import UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.auth import get_current_user
from app.middleware.rate_limit import limiter
from app.config import settings
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from app.models.password_reset_token import PasswordResetToken
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    email = user_data.email.lower().strip()
    _validate_password(user_data.password)
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to register with provided credentials"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hashed_password
    )
    
    import os
    admin_email = os.getenv('ADMIN_EMAIL')
    if admin_email and email == admin_email:
        new_user.is_admin = True
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    email = user_data.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
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


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(f"{token}.{settings.secret_key}".encode("utf-8")).hexdigest()


def _validate_password(password: str) -> None:
    if len(password) < 8 or len(password) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be between 8 and 128 characters")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must include at least one letter and one number")


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = payload.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        token_hash = _hash_reset_token(token)
        expires_at = datetime.utcnow() + timedelta(minutes=60)
        prt = PasswordResetToken(id=uuid.uuid4(), user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        db.add(prt)
        await db.commit()
        reset_url = f"{settings.frontend_base_url}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_url)
    return {"success": True}


@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    _validate_password(payload.new_password)
    token_hash = _hash_reset_token(payload.token.strip())
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    row = result.scalar_one_or_none()
    if not row or row.used_at is not None or row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user_result = await db.execute(select(User).where(User.id == row.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    user.password_hash = get_password_hash(payload.new_password)
    row.used_at = datetime.utcnow()
    await db.commit()
    return {"success": True}


@router.post("/change-password")
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_password(payload.new_password)
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return {"success": True}


@router.get("/debug/admin-status")
async def debug_admin_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if settings.environment == "production" or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
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
