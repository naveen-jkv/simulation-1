from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification, NotificationRead
from app.schemas.auth import UserResponse
from app.utils.auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.get(
    "/stats",
    summary="Dashboard Metrics & Statistics (Admin Only)",
    description="Returns aggregate counts of notifications, categories, priorities, users, and student read interactions.",
)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    total_notifications = db.query(func.count(Notification.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
    total_reads = db.query(func.count(NotificationRead.id)).scalar() or 0

    # Group counts by category
    category_counts_raw = (
        db.query(Notification.category, func.count(Notification.id))
        .group_by(Notification.category)
        .all()
    )
    categories = {cat: count for cat, count in category_counts_raw}

    # Group counts by priority
    priority_counts_raw = (
        db.query(Notification.priority, func.count(Notification.id))
        .group_by(Notification.priority)
        .all()
    )
    priorities = {prio: count for prio, count in priority_counts_raw}

    return {
        "total_notifications": total_notifications,
        "total_users": total_users,
        "total_students": total_students,
        "total_admins": total_admins,
        "total_reads": total_reads,
        "categories": categories,
        "priorities": priorities,
    }


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List Registered Users (Admin Only)",
    description="Retrieve all registered users and roles for management purposes.",
)
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    return db.query(User).order_by(User.created_at.desc()).all()
