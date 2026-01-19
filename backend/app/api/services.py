from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, UploadFile, File
from fastapi.responses import Response
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import timedelta, datetime
from urllib.parse import urlparse
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.service import Service, CheckFrequency
from app.models.change_event import ChangeEvent
from app.models.tag import Tag, service_tags
from app.models.saved_view import SortBy, SortOrder
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.dashboard import DashboardSummaryResponse, ServiceSummary, ChangeEventSummary
from app.core.auth import get_current_user
from app.services.subscription_service import (
    enforce_service_limit,
    validate_check_frequency
)
from app.services.csv_service import (
    parse_services_csv,
    validate_service_row,
    generate_services_csv
)
from app.middleware.rate_limit import limiter
import uuid
import bleach
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["services"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

__all__ = ["router", "dashboard_router"]


def _normalize_url(value: str) -> str:
    url = value.strip()
    if not url or any(ch.isspace() for ch in url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL")
    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        url = f"https://{url}"
        parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL")
    return parsed.geturl()


async def create_initial_snapshot_background(service_id: UUID):
    from app.database import AsyncSessionLocal
    from app.services.snapshot_service import create_snapshot
    from app.services.diff_service import process_new_snapshot
    import traceback
    
    try:
        logger.info(f"Background task started for service {service_id}")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Service).where(Service.id == service_id)
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.error(f"Service {service_id} not found in background task")
                return
            
            logger.info(f"Creating initial snapshot for service {service_id} in background")
            snapshot, created_new = await create_snapshot(db, service)
            logger.info(f"Snapshot {snapshot.id} created, processing changes...")
            
            change_event = None
            if created_new:
                change_event = await process_new_snapshot(db, snapshot)
            if change_event:
                logger.info(f"Change event {change_event.id} created for service {service_id}")
            else:
                logger.info(f"No changes detected for service {service_id} (initial snapshot)")
            
            logger.info(f"Initial snapshot completed successfully for service {service_id}")
    except Exception as e:
        logger.error(f"Failed to create initial snapshot for service {service_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    background_tasks: BackgroundTasks,
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
    sanitized_url = sanitized_url.replace("javascript:", "").strip()
    normalized_url = _normalize_url(sanitized_url)
    
    new_service = Service(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=sanitized_name,
        url=normalized_url,
        check_frequency=service_data.check_frequency,
        alerts_enabled=True,
        alert_confidence_threshold=0.6
    )
    
    if service_data.tag_ids:
        tag_result = await db.execute(
            select(Tag).where(
                Tag.id.in_(service_data.tag_ids),
                Tag.user_id == current_user.id
            )
        )
        tags = tag_result.scalars().all()
        new_service.tags = tags
    
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service, ["tags"])
    
    background_tasks.add_task(create_initial_snapshot_background, new_service.id)
    logger.info(f"Service {new_service.id} created, initial snapshot queued")
    
    return new_service


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    tags: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, created_at, last_checked_at"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Service).where(Service.user_id == current_user.id)
    
    if tags:
        tag_ids = [UUID(t.strip()) for t in tags.split(",") if t.strip()]
        if tag_ids:
            query = query.join(service_tags).join(Tag).where(
                and_(
                    Tag.id.in_(tag_ids),
                    Tag.user_id == current_user.id
                )
            ).distinct()
    
    if is_active is not None:
        query = query.where(Service.is_active == is_active)
    
    if sort_by == "created_at":
        order_col = Service.created_at
    elif sort_by == "last_checked_at":
        order_col = Service.last_checked_at
    else:
        order_col = Service.name
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    result = await db.execute(query)
    services = result.scalars().unique().all()
    
    for service in services:
        await db.refresh(service, ["tags"])
    
    return services


@router.get("/export")
async def export_services(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.user_id == current_user.id).order_by(Service.created_at.desc())
    )
    services = result.scalars().all()
    
    csv_content = generate_services_csv(services)
    
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=services_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_services(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    content = await file.read()
    try:
        csv_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    
    rows = parse_services_csv(csv_content)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or invalid"
        )
    
    created_services = []
    errors = []
    
    for idx, row in enumerate(rows, start=2):
        is_valid, error_msg = validate_service_row(row, idx)
        if not is_valid:
            errors.append(error_msg)
            continue
        
        try:
            await enforce_service_limit(db, current_user.id)
            
            check_freq_str = row.get("check_frequency", "daily").strip().lower()
            check_frequency = CheckFrequency.daily
            if check_freq_str == "weekly":
                check_frequency = CheckFrequency.weekly
            elif check_freq_str == "twice_daily":
                check_frequency = CheckFrequency.twice_daily
            
            await validate_check_frequency(db, current_user.id, check_frequency)
            
            url = row["url"].strip()
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            
            normalized_url = _normalize_url(url)
            
            is_active = row.get("is_active", "true").strip().lower() in ["true", "1", "yes"]
            
            new_service = Service(
                id=uuid.uuid4(),
                user_id=current_user.id,
                name=row["name"].strip(),
                url=normalized_url,
                check_frequency=check_frequency,
                is_active=is_active,
                alerts_enabled=True,
                alert_confidence_threshold=0.6
            )
            
            db.add(new_service)
            await db.commit()
            await db.refresh(new_service, ["tags"])
            
            background_tasks.add_task(create_initial_snapshot_background, new_service.id)
            
            created_services.append(new_service)
        except HTTPException as e:
            errors.append(f"Row {idx}: {e.detail}")
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    return {
        "created": len(created_services),
        "failed": len(errors),
        "errors": errors,
        "services": [ServiceResponse.model_validate(s) for s in created_services]
    }


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
    
    await db.refresh(service, ["tags"])
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
        update_data["url"] = update_data["url"].replace("javascript:", "").strip()
        update_data["url"] = _normalize_url(update_data["url"])
    
    if "check_frequency" in update_data:
        await validate_check_frequency(db, current_user.id, update_data["check_frequency"])
    
    tag_ids = update_data.pop("tag_ids", None)
    
    for field, value in update_data.items():
        setattr(service, field, value)
    
    if tag_ids is not None:
        tag_result = await db.execute(
            select(Tag).where(
                Tag.id.in_(tag_ids),
                Tag.user_id == current_user.id
            )
        )
        tags = tag_result.scalars().all()
        service.tags = tags
    
    await db.commit()
    await db.refresh(service, ["tags"])
    
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
            snapshot, created_new = await create_snapshot(db, service)
            change_event = None
            if created_new:
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
    tags: Optional[str] = Query(None, description="Comma-separated tag IDs"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: Optional[str] = Query("name", description="Sort by: name, created_at, last_checked_at"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Service).where(Service.user_id == current_user.id)
    
    if tags:
        tag_ids = [UUID(t.strip()) for t in tags.split(",") if t.strip()]
        if tag_ids:
            query = query.join(service_tags).join(Tag).where(
                and_(
                    Tag.id.in_(tag_ids),
                    Tag.user_id == current_user.id
                )
            ).distinct()
    
    if is_active is not None:
        query = query.where(Service.is_active == is_active)
    
    if sort_by == "created_at":
        order_col = Service.created_at
    elif sort_by == "last_checked_at":
        order_col = Service.last_checked_at
    else:
        order_col = Service.name
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    result = await db.execute(query)
    services = result.scalars().unique().all()
    
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
    
    def compute_next_check(last_checked_at, check_frequency):
        if not last_checked_at:
            return None
        if check_frequency == CheckFrequency.weekly:
            return last_checked_at + timedelta(days=7)
        if check_frequency == CheckFrequency.twice_daily:
            return last_checked_at + timedelta(hours=12)
        return last_checked_at + timedelta(days=1)

    service_summaries = []
    total_services = len(services)
    active_services = sum(1 for s in services if s.is_active)
    recent_changes_count = 0
    
    for service in services:
        await db.refresh(service, ["tags"])
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
            check_frequency=service.check_frequency,
            last_checked_at=service.last_checked_at,
            next_check_at=compute_next_check(service.last_checked_at, service.check_frequency),
            last_change_event=last_change_event,
            change_count=change_count,
            alerts_enabled=service.alerts_enabled,
            tags=service.tags
        ))
    
    return DashboardSummaryResponse(
        services=service_summaries,
        total_services=total_services,
        active_services=active_services,
        recent_changes_count=recent_changes_count
    )



