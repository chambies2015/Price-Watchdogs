from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID
import logging
from app.models.snapshot import Snapshot
from app.models.service import Service
from app.models.change_event import ChangeEvent

logger = logging.getLogger(__name__)


async def cleanup_old_snapshots(
    db: AsyncSession,
    keep_last_n: int = 50
) -> dict:
    start_time = datetime.utcnow()
    
    stats = {
        "services_processed": 0,
        "snapshots_deleted": 0,
        "snapshots_kept": 0,
        "snapshots_with_change_events": 0,
        "duplicates_removed": 0,
        "errors": []
    }
    
    try:
        result = await db.execute(select(Service))
        services = result.scalars().all()
        
        for service in services:
            try:
                service_stats = await cleanup_service_snapshots(
                    db,
                    service.id,
                    keep_last_n
                )
                
                stats["services_processed"] += 1
                stats["snapshots_deleted"] += service_stats["deleted"]
                stats["snapshots_kept"] += service_stats["kept"]
                stats["snapshots_with_change_events"] += service_stats["with_change_events"]
                stats["duplicates_removed"] += service_stats["duplicates_removed"]
                
            except Exception as e:
                error_msg = f"Error cleaning up snapshots for service {service.id}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                continue
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            f"Cleanup completed in {duration:.2f}s: "
            f"Processed {stats['services_processed']} services, "
            f"Deleted {stats['snapshots_deleted']} snapshots, "
            f"Kept {stats['snapshots_kept']} snapshots, "
            f"Removed {stats['duplicates_removed']} duplicates"
        )
        
        return stats
        
    except Exception as e:
        error_msg = f"Error in cleanup job: {e}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        return stats


async def cleanup_service_snapshots(
    db: AsyncSession,
    service_id: UUID,
    keep_last_n: int = 50
) -> dict:
    service_stats = {
        "deleted": 0,
        "kept": 0,
        "with_change_events": 0,
        "duplicates_removed": 0
    }
    
    result = await db.execute(
        select(ChangeEvent).where(
            ChangeEvent.service_id == service_id
        )
    )
    service_change_events = result.scalars().all()
    
    protected_snapshot_ids = set()
    for event in service_change_events:
        if event.old_snapshot_id:
            protected_snapshot_ids.add(event.old_snapshot_id)
        if event.new_snapshot_id:
            protected_snapshot_ids.add(event.new_snapshot_id)
    
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.service_id == service_id)
        .order_by(Snapshot.created_at.desc())
    )
    all_snapshots = result.scalars().all()
    
    if not all_snapshots:
        return service_stats
    
    hash_groups = {}
    for snapshot in all_snapshots:
        if snapshot.normalized_content_hash not in hash_groups:
            hash_groups[snapshot.normalized_content_hash] = []
        hash_groups[snapshot.normalized_content_hash].append(snapshot)
    
    duplicate_ids_to_delete = set()
    for hash_value, duplicates in hash_groups.items():
        if len(duplicates) > 1:
            duplicates.sort(key=lambda s: s.created_at, reverse=True)
            
            for duplicate in duplicates[1:]:
                duplicate_ids_to_delete.add(duplicate.id)
                service_stats["duplicates_removed"] += 1
    
    for duplicate_id in duplicate_ids_to_delete:
        result = await db.execute(
            select(Snapshot).where(Snapshot.id == duplicate_id)
        )
        duplicate = result.scalar_one_or_none()
        if duplicate:
            await db.delete(duplicate)
    
    await db.commit()
    
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.service_id == service_id)
        .order_by(Snapshot.created_at.desc())
    )
    remaining_snapshots = result.scalars().all()
    
    snapshots_to_keep_ids = set()
    
    for i, snapshot in enumerate(remaining_snapshots):
        if i < keep_last_n:
            snapshots_to_keep_ids.add(snapshot.id)
        if snapshot.id in protected_snapshot_ids:
            snapshots_to_keep_ids.add(snapshot.id)
    
    service_stats["with_change_events"] = len(protected_snapshot_ids)
    
    snapshots_to_delete = [
        s for s in remaining_snapshots
        if s.id not in snapshots_to_keep_ids
    ]
    
    for snapshot in snapshots_to_delete:
        await db.delete(snapshot)
        service_stats["deleted"] += 1
    
    service_stats["kept"] = len(snapshots_to_keep_ids)
    
    await db.commit()
    
    return service_stats

