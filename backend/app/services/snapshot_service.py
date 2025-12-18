from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import UUID
import uuid
import logging
from app.models.snapshot import Snapshot
from app.models.service import Service
from app.services.fetcher import fetch_page, FetchError
from app.services.processor import process_html

logger = logging.getLogger(__name__)


async def create_snapshot(
    db: AsyncSession,
    service: Service,
    custom_selector: str = None
) -> Snapshot:
    try:
        html = await fetch_page(service.url)
        
        raw_hash, normalized_hash, normalized_content = process_html(html, custom_selector)
        
        result = await db.execute(
            select(Snapshot)
            .where(Snapshot.service_id == service.id)
            .order_by(Snapshot.created_at.desc())
            .limit(1)
        )
        last_snapshot = result.scalar_one_or_none()
        
        if last_snapshot and last_snapshot.normalized_content_hash == normalized_hash:
            logger.info(f"No changes detected for service {service.id}")
            service.last_checked_at = datetime.utcnow()
            await db.commit()
            return last_snapshot
        
        snapshot = Snapshot(
            id=uuid.uuid4(),
            service_id=service.id,
            raw_html_hash=raw_hash,
            normalized_content_hash=normalized_hash,
            normalized_content=normalized_content
        )
        
        db.add(snapshot)
        
        service.last_snapshot_id = snapshot.id
        service.last_checked_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(snapshot)
        
        logger.info(f"Created snapshot {snapshot.id} for service {service.id}")
        
        return snapshot
        
    except FetchError as e:
        logger.error(f"Failed to fetch page for service {service.id}: {e}")
        service.last_checked_at = datetime.utcnow()
        await db.commit()
        raise
        
    except Exception as e:
        logger.error(f"Error creating snapshot for service {service.id}: {e}")
        raise


async def get_service_snapshots(
    db: AsyncSession,
    service_id: UUID,
    limit: int = 10
) -> list[Snapshot]:
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.service_id == service_id)
        .order_by(Snapshot.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

