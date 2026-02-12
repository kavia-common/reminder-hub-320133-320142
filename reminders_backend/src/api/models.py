from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ReminderBase(BaseModel):
    """Shared reminder fields used across create/update payloads."""

    title: str = Field(..., min_length=1, max_length=500, description="Reminder title.")
    description: Optional[str] = Field(
        default=None, max_length=5000, description="Optional reminder description."
    )
    due_date: datetime = Field(..., description="Due date/time (timezone-aware).")
    notification_at: Optional[datetime] = Field(
        default=None,
        description="Optional notification date/time (timezone-aware).",
    )


class ReminderCreate(ReminderBase):
    """Payload for creating a reminder."""


class ReminderUpdate(BaseModel):
    """Payload for updating a reminder. All fields optional."""

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=500, description="Reminder title."
    )
    description: Optional[str] = Field(
        default=None, max_length=5000, description="Optional reminder description."
    )
    due_date: Optional[datetime] = Field(
        default=None, description="Due date/time (timezone-aware)."
    )
    notification_at: Optional[datetime] = Field(
        default=None,
        description="Optional notification date/time (timezone-aware).",
    )

    model_config = ConfigDict(extra="forbid")


class ReminderToggleComplete(BaseModel):
    """Payload for toggling completion status."""

    completed: bool = Field(..., description="Whether the reminder is completed.")


class Reminder(ReminderBase):
    """Reminder as stored/returned by the API."""

    id: int = Field(..., description="Reminder ID.")
    completed: bool = Field(..., description="Completion status.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response shape."""

    detail: str = Field(..., description="Human-readable error message.")
