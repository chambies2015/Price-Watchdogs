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
import uuid

router = APIRouter(prefix="/api/services", tags=["services"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

__all__ = ["router", "dashboard_router"]


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_service = Service(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=service_data.name,
        url=service_data.url,
        check_frequency=service_data.check_frequency,
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    
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


@dashboard_router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id)
    )
    services = result.scalars().all()
    
    service_summaries = []
    total_services = len(services)
    active_services = sum(1 for s in services if s.is_active)
    recent_changes_count = 0
    
    for service in services:
        latest_change_result = await db.execute(
            select(ChangeEvent)
            .where(ChangeEvent.service_id == service.id)
            .order_by(ChangeEvent.created_at.desc())
            .limit(1)
        )
        latest_change = latest_change_result.scalar_one_or_none()
        
        change_count_result = await db.execute(
            select(func.count(ChangeEvent.id))
            .where(ChangeEvent.service_id == service.id)
        )
        change_count = change_count_result.scalar_one() or 0
        
        if latest_change:
            recent_changes_count += 1
            last_change_event = ChangeEventSummary(
                id=latest_change.id,
                change_type=latest_change.change_type,
                summary=latest_change.summary,
                confidence_score=latest_change.confidence_score,
                created_at=latest_change.created_at
            )
        else:
            last_change_event = None
        
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

