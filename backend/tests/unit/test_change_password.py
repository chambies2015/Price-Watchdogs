import pytest
from sqlalchemy import select
import uuid

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_change_password_requires_auth(client):
    resp = await client.post("/api/auth/change-password", json={"current_password": "x", "new_password": "newpassword123"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_updates_hash(client, db_session):
    user_id = uuid.uuid4()
    user = User(id=user_id, email="cp@example.com", password_hash=get_password_hash("oldpassword123"))
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"current_password": "oldpassword123", "new_password": "newpassword123"},
    )
    assert resp.status_code == 200

    refreshed = await db_session.execute(select(User).where(User.id == user_id))
    u2 = refreshed.scalar_one()
    assert verify_password("newpassword123", u2.password_hash)

