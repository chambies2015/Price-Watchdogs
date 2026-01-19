import csv
import io
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from uuid import UUID
from app.models.service import Service, CheckFrequency
from app.models.change_event import ChangeEvent
from app.models.snapshot import Snapshot
import logging

logger = logging.getLogger(__name__)


def parse_services_csv(csv_content: str) -> List[Dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = []
    for row in reader:
        rows.append({k.strip(): v.strip() if v else "" for k, v in row.items()})
    return rows


def validate_service_row(row: Dict[str, str], row_num: int) -> Tuple[bool, Optional[str]]:
    if not row.get("name", "").strip():
        return False, f"Row {row_num}: 'name' is required"
    
    if not row.get("url", "").strip():
        return False, f"Row {row_num}: 'url' is required"
    
    url = row["url"].strip()
    
    if url.startswith(("javascript:", "data:", "file:")):
        return False, f"Row {row_num}: Invalid URL scheme"
    
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False, f"Row {row_num}: Invalid URL scheme"
        if not parsed.netloc or len(parsed.netloc.strip()) == 0:
            return False, f"Row {row_num}: Invalid URL format"
        if "." not in parsed.netloc or parsed.netloc.startswith(".") or parsed.netloc.endswith("."):
            return False, f"Row {row_num}: Invalid URL format"
    except Exception:
        return False, f"Row {row_num}: Invalid URL format"
    
    check_frequency = row.get("check_frequency", "daily").strip().lower()
    if check_frequency and check_frequency not in ["daily", "weekly", "twice_daily"]:
        return False, f"Row {row_num}: Invalid check_frequency (must be daily, weekly, or twice_daily)"
    
    is_active = row.get("is_active", "true").strip().lower()
    if is_active and is_active not in ["true", "false", "1", "0", "yes", "no"]:
        return False, f"Row {row_num}: Invalid is_active (must be true/false)"
    
    return True, None


def generate_services_csv(services: List[Service]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "name", "url", "check_frequency", "is_active", 
        "alerts_enabled", "created_at", "last_checked_at"
    ])
    
    for service in services:
        writer.writerow([
            str(service.id),
            service.name,
            service.url,
            service.check_frequency.value,
            "true" if service.is_active else "false",
            "true" if service.alerts_enabled else "false",
            service.created_at.isoformat() if service.created_at else "",
            service.last_checked_at.isoformat() if service.last_checked_at else ""
        ])
    
    return output.getvalue()


def generate_change_events_csv(events: List[ChangeEvent], service_names: Dict[UUID, str]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "service_id", "service_name", "change_type", "summary", 
        "confidence_score", "created_at"
    ])
    
    for event in events:
        writer.writerow([
            str(event.id),
            str(event.service_id),
            service_names.get(event.service_id, "Unknown"),
            event.change_type.value,
            event.summary,
            str(event.confidence_score),
            event.created_at.isoformat() if event.created_at else ""
        ])
    
    return output.getvalue()


def generate_snapshots_csv(snapshots: List[Snapshot], service_names: Dict[UUID, str]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "service_id", "service_name", "created_at", "content_hash"
    ])
    
    for snapshot in snapshots:
        writer.writerow([
            str(snapshot.id),
            str(snapshot.service_id),
            service_names.get(snapshot.service_id, "Unknown"),
            snapshot.created_at.isoformat() if snapshot.created_at else "",
            snapshot.normalized_content_hash
        ])
    
    return output.getvalue()
