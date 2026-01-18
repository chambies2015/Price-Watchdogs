from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.service import Service
from app.models.change_event import ChangeEvent
from app.schemas.snapshot import SnapshotResponse
from app.schemas.change_event import ChangeEventResponse, ChangeEventDetailResponse
from app.models.snapshot import Snapshot
from app.core.auth import get_current_user
from app.services.snapshot_service import get_service_snapshots, create_snapshot
from app.services.diff_service import process_new_snapshot

router = APIRouter(prefix="/api/services", tags=["snapshots"])


@router.get("/{service_id}/snapshots", response_model=List[SnapshotResponse])
async def list_service_snapshots(
    service_id: UUID,
    limit: int = 10,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    limit = max(1, min(limit, 100))
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
    response.headers["Cache-Control"] = "private, max-age=30"
    response.headers["Vary"] = "Authorization"
    return snapshots


@router.get("/{service_id}/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    service_id: UUID,
    snapshot_id: UUID,
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
    
    result = await db.execute(
        select(Snapshot).where(
            Snapshot.id == snapshot_id,
            Snapshot.service_id == service_id
        )
    )
    snapshot = result.scalar_one_or_none()
    
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found"
        )
    
    return snapshot


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
        snapshot, created_new = await create_snapshot(db, service)
        
        try:
            if created_new:
                await process_new_snapshot(db, snapshot)
        except Exception as e:
            pass
        
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/{service_id}/changes", response_model=List[ChangeEventResponse])
async def list_service_changes(
    service_id: UUID,
    limit: int = 20,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    limit = max(1, min(limit, 100))
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
    
    result = await db.execute(
        select(ChangeEvent)
        .where(ChangeEvent.service_id == service_id)
        .order_by(ChangeEvent.created_at.desc())
        .limit(limit)
    )
    changes = result.scalars().all()
    response.headers["Cache-Control"] = "private, max-age=30"
    response.headers["Vary"] = "Authorization"
    return changes


@router.get("/changes/{change_id}", response_model=ChangeEventDetailResponse)
async def get_change_event(
    change_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChangeEvent).where(ChangeEvent.id == change_id)
    )
    change_event = result.scalar_one_or_none()
    
    if not change_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change event not found"
        )
    
    result = await db.execute(
        select(Service).where(
            Service.id == change_event.service_id,
            Service.user_id == current_user.id
        )
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    old_snapshot = None
    if change_event.old_snapshot_id:
        result = await db.execute(
            select(Snapshot).where(Snapshot.id == change_event.old_snapshot_id)
        )
        old_snapshot = result.scalar_one_or_none()
    
    result = await db.execute(
        select(Snapshot).where(Snapshot.id == change_event.new_snapshot_id)
    )
    new_snapshot = result.scalar_one_or_none()
    
    if not new_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New snapshot not found"
        )
    
    return ChangeEventDetailResponse(
        id=change_event.id,
        service_id=change_event.service_id,
        old_snapshot_id=change_event.old_snapshot_id,
        new_snapshot_id=change_event.new_snapshot_id,
        change_type=change_event.change_type,
        summary=change_event.summary,
        confidence_score=change_event.confidence_score,
        created_at=change_event.created_at,
        old_snapshot=SnapshotResponse(
            id=old_snapshot.id,
            service_id=old_snapshot.service_id,
            raw_html_hash=old_snapshot.raw_html_hash,
            normalized_content_hash=old_snapshot.normalized_content_hash,
            normalized_content=old_snapshot.normalized_content,
            created_at=old_snapshot.created_at
        ) if old_snapshot else None,
        new_snapshot=SnapshotResponse(
            id=new_snapshot.id,
            service_id=new_snapshot.service_id,
            raw_html_hash=new_snapshot.raw_html_hash,
            normalized_content_hash=new_snapshot.normalized_content_hash,
            normalized_content=new_snapshot.normalized_content,
            created_at=new_snapshot.created_at
        )
    )

