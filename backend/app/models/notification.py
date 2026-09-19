from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    original_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="General", index=True)
    priority = Column(String(20), nullable=False, default="Medium", index=True)
    deadline = Column(String(50), nullable=True)  # Format: YYYY-MM-DD or None
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    creator = relationship("User", back_populates="created_notifications")
    reads = relationship("NotificationRead", back_populates="notification", cascade="all, delete-orphan")


class NotificationRead(Base):
    __tablename__ = "notification_reads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(
        Integer,
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    read_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("notification_id", "user_id", name="uq_notification_user_read"),
    )

    # Relationships
    notification = relationship("Notification", back_populates="reads")
    user = relationship("User", back_populates="reads")
