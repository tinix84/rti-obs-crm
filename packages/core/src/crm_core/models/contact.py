"""Contact model – maps to vault/contacts/*.md frontmatter."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactStatus(StrEnum):
    LEAD = "lead"
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    CHURNED = "churned"


class Contact(BaseModel):
    """A CRM contact backed by a vault markdown note."""

    id: str = Field(..., description="Unique slug identifier, e.g. cnt-001")
    name: str = Field(..., min_length=1)
    email: EmailStr | None = None
    phone: str | None = None
    company: str | None = None
    company_id: str | None = None
    status: ContactStatus = ContactStatus.LEAD
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    owner: str | None = None
    linkedin: str | None = None
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
        """Return a dict suitable for writing back to YAML frontmatter."""
        data = self.model_dump(mode="json")
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["status"] = self.status.value
        return data
