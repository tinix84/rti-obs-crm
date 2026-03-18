"""Task model – maps to vault/tasks/*.md frontmatter."""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(BaseModel):
    """A CRM task backed by a vault markdown note."""

    id: str = Field(..., description="Unique slug identifier, e.g. tsk-001")
    title: str = Field(..., min_length=1)
    contact_id: str | None = None
    deal_id: str | None = None
    status: TaskStatus = TaskStatus.OPEN
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date_type | None = None
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return list(v)

    def to_frontmatter(self) -> dict:
        data = self.model_dump(mode="json")
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        if self.due_date:
            data["due_date"] = self.due_date.isoformat()
        return data
