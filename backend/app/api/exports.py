from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.service import Service
from app.models.change_event import ChangeEvent
from app.models.snapshot import Snapshot
from app.schemas.change_event import ChangeEventResponse
from app.schemas.snapshot import SnapshotResponse
from app.core.auth import get_current_user
from app.services.csv_service import (
    generate_change_events_csv,
    generate_snapshots_csv
)
from app.middleware.rate_limit import limiter
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/services/{service_id}/changes.csv")
@limiter.limit("20/minute")
async def export_service_changes_csv(
    request: Request,
    service_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
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
    
    query = select(ChangeEvent).where(ChangeEvent.service_id == service_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(ChangeEvent.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    service_names = {service_id: service.name}
    csv_content = generate_change_events_csv(events, service_names)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=changes_{service_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/services/{service_id}/changes.json")
@limiter.limit("20/minute")
async def export_service_changes_json(
    request: Request,
    service_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
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
    
    query = select(ChangeEvent).where(ChangeEvent.service_id == service_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(ChangeEvent.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return JSONResponse(
        content=[ChangeEventResponse.model_validate(e).model_dump() for e in events]
    )


@router.get("/services/{service_id}/snapshots.csv")
@limiter.limit("20/minute")
async def export_service_snapshots_csv(
    request: Request,
    service_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
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
    
    query = select(Snapshot).where(Snapshot.service_id == service_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(Snapshot.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(Snapshot.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(Snapshot.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    snapshots = result.scalars().all()
    
    service_names = {service_id: service.name}
    csv_content = generate_snapshots_csv(snapshots, service_names)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=snapshots_{service_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/services/{service_id}/snapshots.json")
@limiter.limit("20/minute")
async def export_service_snapshots_json(
    request: Request,
    service_id: UUID,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
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
    
    query = select(Snapshot).where(Snapshot.service_id == service_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(Snapshot.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(Snapshot.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(Snapshot.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    snapshots = result.scalars().all()
    
    return JSONResponse(
        content=[SnapshotResponse.model_validate(s).model_dump() for s in snapshots]
    )


@router.get("/all/changes.csv")
@limiter.limit("10/minute")
async def export_all_changes_csv(
    request: Request,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id)
    )
    services = result.scalars().all()
    service_ids = [s.id for s in services]
    service_names = {s.id: s.name for s in services}
    
    if not service_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No services found"
        )
    
    query = select(ChangeEvent).where(ChangeEvent.service_id.in_(service_ids))
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(ChangeEvent.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    csv_content = generate_change_events_csv(events, service_names)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=all_changes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/all/changes.json")
@limiter.limit("10/minute")
async def export_all_changes_json(
    request: Request,
    limit: int = Query(1000, ge=1, le=10000),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id)
    )
    services = result.scalars().all()
    service_ids = [s.id for s in services]
    
    if not service_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No services found"
        )
    
    query = select(ChangeEvent).where(ChangeEvent.service_id.in_(service_ids))
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(ChangeEvent.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    query = query.order_by(ChangeEvent.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return JSONResponse(
        content=[ChangeEventResponse.model_validate(e).model_dump() for e in events]
    )
