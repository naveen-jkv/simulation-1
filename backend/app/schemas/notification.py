from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

# Allowed categories and priorities
NotificationCategory = Literal[
    "Academic",
    "Exam",
    "Assignment",
    "Placement",
    "Fees",
    "Event",
    "Holiday",
    "General",
]

NotificationPriority = Literal["Low", "Medium", "High"]


class AIAnalysisOutput(BaseModel):
    summary: str = Field(..., description="1-2 sentence concise summary of the notification")
    category: NotificationCategory = Field(
        ...,
        description="Category: Academic, Exam, Assignment, Placement, Fees, Event, Holiday, General",
    )
    priority: NotificationPriority = Field(
        ...,
        description="Priority: Low, Medium, High",
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Deadline in YYYY-MM-DD format if applicable, otherwise None",
    )


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, examples=["Placement Training Registration"])
    content: Optional[str] = Field(
        default=None,
        min_length=5,
        description="The full notification announcement text (alias for original_content)",
        examples=["All final year students must register for the mandatory corporate placement training before Friday 2026-09-25."],
    )
    original_content: Optional[str] = Field(
        default=None,
        description="Alternative field name for content",
    )
    # Optional manual overrides (if admin wishes to skip or override AI)
    category: Optional[NotificationCategory] = None
    priority: Optional[NotificationPriority] = None
    deadline: Optional[str] = None

    @model_validator(mode="after")
    def validate_content_present(self):
        if not self.content and not self.original_content:
            raise ValueError("Either 'content' or 'original_content' must be provided.")
        if not self.content and self.original_content:
            self.content = self.original_content
        elif not self.original_content and self.content:
            self.original_content = self.content
        return self


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    content: Optional[str] = Field(None, min_length=5)
    original_content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[NotificationCategory] = None
    priority: Optional[NotificationPriority] = None
    deadline: Optional[str] = None
    rerun_ai: Optional[bool] = Field(
        default=False,
        description="Set to true to re-analyze content using the AI service",
    )

    @model_validator(mode="after")
    def sync_content(self):
        if self.content and not self.original_content:
            self.original_content = self.content
        elif self.original_content and not self.content:
            self.content = self.original_content
        return self


class NotificationResponse(BaseModel):
    id: int
    title: str
    summary: str
    category: str
    priority: str
    deadline: Optional[str] = None
    is_read: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationDetailResponse(NotificationResponse):
    original_content: str
    created_by: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationFilterParams(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    search: Optional[str] = None
    is_read: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
