from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate, SavedViewUpdate, SavedViewResponse
from app.core.auth import get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/saved-views", tags=["saved-views"])


@router.get("", response_model=List[SavedViewResponse])
async def list_saved_views(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedView).where(SavedView.user_id == current_user.id).order_by(SavedView.created_at.desc())
    )
    views = result.scalars().all()
    response_views = []
    for view in views:
        filter_tags = None
        if view.filter_tags:
            try:
                filter_tags = [UUID(tag_id) for tag_id in view.filter_tags]
            except (ValueError, TypeError):
                filter_tags = None
        response_views.append(SavedViewResponse(
            id=view.id,
            user_id=view.user_id,
            name=view.name,
            filter_tags=filter_tags,
            filter_active=view.filter_active,
            sort_by=view.sort_by,
            sort_order=view.sort_order,
            created_at=view.created_at
        ))
    return response_views


@router.post("", response_model=SavedViewResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_view(
    view_data: SavedViewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedView).where(
            SavedView.user_id == current_user.id,
            SavedView.name == view_data.name
        )
    )
    existing_view = result.scalar_one_or_none()
    
    if existing_view:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saved view with this name already exists"
        )
    
    new_view = SavedView(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=view_data.name,
        filter_tags=[str(tag_id) for tag_id in view_data.filter_tags] if view_data.filter_tags else [],
        filter_active=view_data.filter_active,
        sort_by=view_data.sort_by,
        sort_order=view_data.sort_order
    )
    
    db.add(new_view)
    await db.commit()
    await db.refresh(new_view)
    
    filter_tags = None
    if new_view.filter_tags:
        try:
            filter_tags = [UUID(tag_id) for tag_id in new_view.filter_tags]
        except (ValueError, TypeError):
            filter_tags = None
    
    return SavedViewResponse(
        id=new_view.id,
        user_id=new_view.user_id,
        name=new_view.name,
        filter_tags=filter_tags,
        filter_active=new_view.filter_active,
        sort_by=new_view.sort_by,
        sort_order=new_view.sort_order,
        created_at=new_view.created_at
    )


@router.put("/{view_id}", response_model=SavedViewResponse)
async def update_saved_view(
    view_id: UUID,
    view_data: SavedViewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == current_user.id
        )
    )
    view = result.scalar_one_or_none()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved view not found"
        )
    
    if view_data.name is not None:
        result = await db.execute(
            select(SavedView).where(
                SavedView.user_id == current_user.id,
                SavedView.name == view_data.name,
                SavedView.id != view_id
            )
        )
        existing_view = result.scalar_one_or_none()
        if existing_view:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Saved view with this name already exists"
            )
        view.name = view_data.name
    
    if view_data.filter_tags is not None:
        view.filter_tags = [str(tag_id) for tag_id in view_data.filter_tags] if view_data.filter_tags else []
    
    if view_data.filter_active is not None:
        view.filter_active = view_data.filter_active
    
    if view_data.sort_by is not None:
        view.sort_by = view_data.sort_by
    
    if view_data.sort_order is not None:
        view.sort_order = view_data.sort_order
    
    await db.commit()
    await db.refresh(view)
    
    filter_tags = None
    if view.filter_tags:
        try:
            filter_tags = [UUID(tag_id) for tag_id in view.filter_tags]
        except (ValueError, TypeError):
            filter_tags = None
    
    return SavedViewResponse(
        id=view.id,
        user_id=view.user_id,
        name=view.name,
        filter_tags=filter_tags,
        filter_active=view.filter_active,
        sort_by=view.sort_by,
        sort_order=view.sort_order,
        created_at=view.created_at
    )


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_view(
    view_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == current_user.id
        )
    )
    view = result.scalar_one_or_none()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved view not found"
        )
    
    await db.delete(view)
    await db.commit()
    
    return None


@router.get("/{view_id}", response_model=SavedViewResponse)
async def get_saved_view(
    view_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == current_user.id
        )
    )
    view = result.scalar_one_or_none()
    
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved view not found"
        )
    
    filter_tags = None
    if view.filter_tags:
        try:
            filter_tags = [UUID(tag_id) for tag_id in view.filter_tags]
        except (ValueError, TypeError):
            filter_tags = None
    
    return SavedViewResponse(
        id=view.id,
        user_id=view.user_id,
        name=view.name,
        filter_tags=filter_tags,
        filter_active=view.filter_active,
        sort_by=view.sort_by,
        sort_order=view.sort_order,
        created_at=view.created_at
    )
