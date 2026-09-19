from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification, NotificationRead
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationDetailResponse,
)
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user, get_current_admin_user, get_optional_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="List Notifications",
    description="Retrieve notifications with optional filtering by category, priority, search text, or read status. Supports pagination.",
)
def list_notifications(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'exam', 'placement', 'academic')"),
    priority: Optional[str] = Query(None, description="Filter by priority (e.g., 'low', 'medium', 'high')"),
    search: Optional[str] = Query(None, description="Search keyword in title, summary, or content"),
    is_read: Optional[bool] = Query(None, description="Filter by read status (true for read, false for unread)"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    current_user_id = current_user.id if current_user else -1

    # Base query joining Notification with NotificationRead for the current user
    query = db.query(
        Notification,
        (NotificationRead.id.isnot(None)).label("user_is_read"),
    ).outerjoin(
        NotificationRead,
        (NotificationRead.notification_id == Notification.id)
        & (NotificationRead.user_id == current_user_id),
    )

    # Apply Category filter (case-insensitive)
    if category:
        query = query.filter(Notification.category.ilike(category.strip()))

    # Apply Priority filter (case-insensitive)
    if priority:
        query = query.filter(Notification.priority.ilike(priority.strip()))

    # Apply Keyword Search filter across title, summary, and original content
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Notification.title.ilike(search_pattern),
                Notification.summary.ilike(search_pattern),
                Notification.original_content.ilike(search_pattern),
            )
        )

    # Apply Read / Unread filter
    if is_read is not None:
        if is_read:
            query = query.filter(NotificationRead.id.isnot(None))
        else:
            query = query.filter(NotificationRead.id.is_(None))

    # Order newest first
    query = query.order_by(desc(Notification.created_at))

    results = query.offset(skip).limit(limit).all()

    # Format response matching exact schema
    response_list = []
    for notif, user_read in results:
        response_list.append(
            NotificationResponse(
                id=notif.id,
                title=notif.title,
                summary=notif.summary,
                category=notif.category,
                priority=notif.priority,
                deadline=notif.deadline,
                is_read=bool(user_read),
                created_at=notif.created_at,
            )
        )

    return response_list


@router.get(
    "/{id}",
    response_model=NotificationDetailResponse,
    summary="Get Notification Details",
    description="Retrieve a single notification by ID with full content and read status for the current user.",
)
def get_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {id} not found",
        )

    # Check read status for current user
    is_read = False
    if current_user:
        read_entry = (
            db.query(NotificationRead)
            .filter(
                NotificationRead.notification_id == notif.id,
                NotificationRead.user_id == current_user.id,
            )
            .first()
        )
        is_read = read_entry is not None

    return NotificationDetailResponse(
        id=notif.id,
        title=notif.title,
        original_content=notif.original_content,
        summary=notif.summary,
        category=notif.category,
        priority=notif.priority,
        deadline=notif.deadline,
        is_read=is_read,
        created_by=notif.created_by,
        created_at=notif.created_at,
        updated_at=notif.updated_at,
    )


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Notification (Admin Only)",
    description="Create a new notification. Analyzes the content with AI to extract summary, category, priority, and deadline. Guaranteed to succeed even if AI service is unavailable.",
)
def create_notification(
    notif_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    content = notif_in.content or notif_in.original_content or ""

    # Call AI service (returns validated structured data or heuristic fallback)
    ai_result = ai_service.analyze_notification(
        title=notif_in.title,
        content=content,
        manual_category=notif_in.category,
        manual_priority=notif_in.priority,
        manual_deadline=notif_in.deadline,
    )

    new_notif = Notification(
        title=notif_in.title.strip(),
        original_content=content.strip(),
        summary=ai_result.summary,
        category=ai_result.category,
        priority=ai_result.priority,
        deadline=ai_result.deadline,
        created_by=current_admin.id,
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    return NotificationResponse(
        id=new_notif.id,
        title=new_notif.title,
        summary=new_notif.summary,
        category=new_notif.category,
        priority=new_notif.priority,
        deadline=new_notif.deadline,
        is_read=False,
        created_at=new_notif.created_at,
    )


@router.put(
    "/{id}",
    response_model=NotificationResponse,
    summary="Update Notification (Admin Only)",
    description="Update an existing notification. Optionally triggers re-analysis if rerun_ai is set to true.",
)
def update_notification(
    id: int,
    notif_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {id} not found",
        )

    # Check if title or content changed
    if notif_update.title is not None:
        notif.title = notif_update.title.strip()
    if notif_update.original_content is not None:
        notif.original_content = notif_update.original_content.strip()

    # Re-run AI if requested
    if notif_update.rerun_ai:
        ai_result = ai_service.analyze_notification(
            title=notif.title,
            content=notif.original_content,
            manual_category=notif_update.category,
            manual_priority=notif_update.priority,
            manual_deadline=notif_update.deadline,
        )
        notif.summary = ai_result.summary
        notif.category = ai_result.category
        notif.priority = ai_result.priority
        notif.deadline = ai_result.deadline
    else:
        if notif_update.summary is not None:
            notif.summary = notif_update.summary.strip()
        if notif_update.category is not None:
            notif.category = notif_update.category
        if notif_update.priority is not None:
            notif.priority = notif_update.priority
        if notif_update.deadline is not None:
            notif.deadline = notif_update.deadline

    db.commit()
    db.refresh(notif)

    # Check read status for current user
    read_entry = (
        db.query(NotificationRead)
        .filter(
            NotificationRead.notification_id == notif.id,
            NotificationRead.user_id == current_admin.id,
        )
        .first()
    )

    return NotificationResponse(
        id=notif.id,
        title=notif.title,
        summary=notif.summary,
        category=notif.category,
        priority=notif.priority,
        deadline=notif.deadline,
        is_read=read_entry is not None,
        created_at=notif.created_at,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Notification (Admin Only)",
    description="Permanently delete a notification and associated read tracking records.",
)
def delete_notification(
    id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {id} not found",
        )

    db.delete(notif)
    db.commit()
    return {"message": f"Notification {id} deleted successfully", "id": id}


@router.put(
    "/{id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
    description="Marks the specified notification as read for the currently authenticated user.",
)
def mark_as_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {id} not found",
        )

    # Check if already marked as read
    existing_read = (
        db.query(NotificationRead)
        .filter(
            NotificationRead.notification_id == notif.id,
            NotificationRead.user_id == current_user.id,
        )
        .first()
    )

    if not existing_read:
        new_read = NotificationRead(
            notification_id=notif.id,
            user_id=current_user.id,
        )
        db.add(new_read)
        db.commit()

    return NotificationResponse(
        id=notif.id,
        title=notif.title,
        summary=notif.summary,
        category=notif.category,
        priority=notif.priority,
        deadline=notif.deadline,
        is_read=True,
        created_at=notif.created_at,
    )
