from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.service import Service
from app.schemas.snapshot import SnapshotResponse
from app.core.auth import get_current_user
from app.services.snapshot_service import get_service_snapshots, create_snapshot

router = APIRouter(prefix="/api/services", tags=["snapshots"])


@router.get("/{service_id}/snapshots", response_model=List[SnapshotResponse])
async def list_service_snapshots(
    service_id: UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.user_id == current_user.id
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    snapshots = await get_service_snapshots(db, service_id, limit)
    return snapshots


@router.post("/{service_id}/snapshots/trigger", response_model=SnapshotResponse)
async def trigger_snapshot(
    service_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.user_id == current_user.id
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    try:
        snapshot = await create_snapshot(db, service)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )

