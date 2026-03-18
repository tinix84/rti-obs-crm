"""Company model – maps to vault/companies/*.md frontmatter."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class Company(BaseModel):
    """A company / account backed by a vault markdown note."""

    id: str = Field(..., description="Unique slug identifier, e.g. cmp-001")
    name: str = Field(..., min_length=1)
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    address: str | None = None
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
        return data
