"""Deal model – maps to vault/deals/*.md frontmatter."""

from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type

from pydantic import BaseModel, Field, field_validator


class Deal(BaseModel):
    """A sales deal / opportunity backed by a vault markdown note."""

    id: str = Field(..., description="Unique slug identifier, e.g. deal-001")
    title: str = Field(..., min_length=1)
    contact_id: str | None = None
    contact_name: str | None = None
    company_id: str | None = None
    company_name: str | None = None
    stage: str = "lead"
    value: float = Field(default=0.0, ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    probability: float = Field(default=0.10, ge=0.0, le=1.0)
    close_date: date_type | None = None
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

    @property
    def weighted_value(self) -> float:
        """Value × probability (used for revenue forecasting)."""
        return self.value * self.probability

    def to_frontmatter(self) -> dict:
        data = self.model_dump(mode="json")
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.close_date:
            data["close_date"] = self.close_date.isoformat()
        return data
