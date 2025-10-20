import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl

from app.core.database import Category, Condition


class ListingBase(BaseModel):
    title: str = Field(max_length=50)
    price: Decimal = Field(default=Decimal("0.00"))
    category: Category
    condition: Condition
    is_active: bool
    description: str
    thumbnail_url: HttpUrl | None = None


class ListingCreate(ListingBase):
    """Schema for creating new listing."""


class ListingUpdate(BaseModel):
    title: str | None = Field(None, max_length=50)
    description: str | None = Field(None)
    price: Decimal | None = Field(None, default=Decimal("0.00"))
    category: Category | None = None
    condition: Condition | None = None
    thumbnail_url: HttpUrl | None = None
    is_active: bool | None = None


class ListingPublic(ListingBase):
    id: uuid.UUID
    seller_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
