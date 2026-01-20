import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid
import hashlib

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.config import settings


@pytest.mark.asyncio
async def test_forgot_password_does_not_leak_user_existence(client, db_session):
    resp1 = await client.post("/api/auth/forgot-password", json={"email": "nope@example.com"})
    assert resp1.status_code == 200

    u = User(id=uuid.uuid4(), email="exists@example.com", password_hash=get_password_hash("oldpassword123"))
    db_session.add(u)
    await db_session.commit()

    resp2 = await client.post("/api/auth/forgot-password", json={"email": "exists@example.com"})
    assert resp2.status_code == 200


@pytest.mark.asyncio
@patch("app.api.auth.send_password_reset_email", new_callable=AsyncMock)
async def test_reset_password_token_flow(mock_send, client, db_session):
    u = User(id=uuid.uuid4(), email="exists2@example.com", password_hash=get_password_hash("oldpassword123"))
    db_session.add(u)
    await db_session.commit()

    resp = await client.post("/api/auth/forgot-password", json={"email": "exists2@example.com"})
    assert resp.status_code == 200
    assert mock_send.await_count == 1
    reset_url = mock_send.await_args.args[1]
    token = reset_url.split("token=", 1)[1]

    reset_resp = await client.post("/api/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
    assert reset_resp.status_code == 200

    refreshed = await db_session.execute(select(User).where(User.id == u.id))
    u2 = refreshed.scalar_one()
    assert verify_password("newpassword123", u2.password_hash)

    again = await client.post("/api/auth/reset-password", json={"token": token, "new_password": "anotherpassword123"})
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token(client, db_session):
    u = User(id=uuid.uuid4(), email="exists3@example.com", password_hash=get_password_hash("oldpassword123"))
    db_session.add(u)
    await db_session.commit()

    token = "expiredtoken"
    token_hash = hashlib.sha256(f"{token}.{settings.secret_key}".encode("utf-8")).hexdigest()
    prt = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=u.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        created_at=datetime.utcnow(),
    )
    db_session.add(prt)
    await db_session.commit()

    resp = await client.post("/api/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
    assert resp.status_code == 400

