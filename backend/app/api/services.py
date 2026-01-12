from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.service import Service, CheckFrequency
from app.models.change_event import ChangeEvent
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.dashboard import DashboardSummaryResponse, ServiceSummary, ChangeEventSummary
from app.core.auth import get_current_user
from app.services.subscription_service import (
    enforce_service_limit,
    validate_check_frequency
)
import uuid
import bleach

router = APIRouter(prefix="/api/services", tags=["services"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

__all__ = ["router", "dashboard_router"]


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await enforce_service_limit(db, current_user.id)
    await validate_check_frequency(db, current_user.id, service_data.check_frequency)
    
    sanitized_name = bleach.clean(service_data.name, tags=[], strip=True)
    sanitized_name = sanitized_name.replace("javascript:", "").strip()
    if not sanitized_name:
        sanitized_name = "Untitled Service"
    
    sanitized_url = bleach.clean(service_data.url, tags=[], strip=True)
    
    new_service = Service(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=sanitized_name,
        url=sanitized_url,
        check_frequency=service_data.check_frequency,
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    
    try:
        from app.services.snapshot_service import create_snapshot
        await create_snapshot(db, new_service)
    except Exception as e:
        pass
    
    return new_service


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id)
    )
    services = result.scalars().all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
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
    
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
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
    
    update_data = service_data.model_dump(exclude_unset=True)
    
    if "name" in update_data:
        update_data["name"] = bleach.clean(update_data["name"], tags=[], strip=True)
        update_data["name"] = update_data["name"].replace("javascript:", "").strip()
        if not update_data["name"]:
            update_data["name"] = "Untitled Service"
    
    if "url" in update_data:
        update_data["url"] = bleach.clean(update_data["url"], tags=[], strip=True)
    
    if "check_frequency" in update_data:
        await validate_check_frequency(db, current_user.id, update_data["check_frequency"])
    
    for field, value in update_data.items():
        setattr(service, field, value)
    
    await db.commit()
    await db.refresh(service)
    
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
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
    
    await db.delete(service)
    await db.commit()
    
    return None


@router.post("/{service_id}/check", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_check(
    service_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual checks are only available for admin users"
        )
    
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
    
    from app.services.snapshot_service import create_snapshot
    from app.services.diff_service import process_new_snapshot
    import asyncio
    
    async def run_check():
        try:
            snapshot = await create_snapshot(db, service)
            change_event = await process_new_snapshot(db, snapshot)
            return {
                "success": True,
                "snapshot_id": str(snapshot.id),
                "change_detected": change_event is not None,
                "change_id": str(change_event.id) if change_event else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    result = await run_check()
    return result


@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id)
    )
    services = result.scalars().all()
    
    service_ids = [s.id for s in services]
    
    if service_ids:
        latest_changes_subquery = (
            select(
                ChangeEvent.service_id,
                ChangeEvent.id,
                ChangeEvent.change_type,
                ChangeEvent.summary,
                ChangeEvent.confidence_score,
                ChangeEvent.created_at,
                func.row_number()
                .over(
                    partition_by=ChangeEvent.service_id,
                    order_by=ChangeEvent.created_at.desc()
                )
                .label("rn")
            )
            .where(ChangeEvent.service_id.in_(service_ids))
            .subquery()
        )
        
        latest_changes_result = await db.execute(
            select(latest_changes_subquery)
            .where(latest_changes_subquery.c.rn == 1)
        )
        latest_changes = {row.service_id: row for row in latest_changes_result.all()}
        
        change_counts_result = await db.execute(
            select(
                ChangeEvent.service_id,
                func.count(ChangeEvent.id).label("count")
            )
            .where(ChangeEvent.service_id.in_(service_ids))
            .group_by(ChangeEvent.service_id)
        )
        change_counts = {row.service_id: row.count for row in change_counts_result.all()}
    else:
        latest_changes = {}
        change_counts = {}
    
    service_summaries = []
    total_services = len(services)
    active_services = sum(1 for s in services if s.is_active)
    recent_changes_count = 0
    
    for service in services:
        latest_change_row = latest_changes.get(service.id)
        
        if latest_change_row:
            recent_changes_count += 1
            last_change_event = ChangeEventSummary(
                id=latest_change_row.id,
                change_type=latest_change_row.change_type,
                summary=latest_change_row.summary,
                confidence_score=latest_change_row.confidence_score,
                created_at=latest_change_row.created_at
            )
        else:
            last_change_event = None
        
        change_count = change_counts.get(service.id, 0)
        
        service_summaries.append(ServiceSummary(
            id=service.id,
            name=service.name,
            url=service.url,
            is_active=service.is_active,
            last_checked_at=service.last_checked_at,
            last_change_event=last_change_event,
            change_count=change_count,
            alerts_enabled=service.alerts_enabled
        ))
    
    return DashboardSummaryResponse(
        services=service_summaries,
        total_services=total_services,
        active_services=active_services,
        recent_changes_count=recent_changes_count
    )

