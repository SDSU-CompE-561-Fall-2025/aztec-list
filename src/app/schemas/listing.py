import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.core.database import Category, Condition


class ListingBase(BaseModel):
    title: str = Field(max_length=50)
    price: float = Field(ge=0.0)
    category: Category
    condition: Condition
    is_active: bool


class ListingCreate(ListingBase):
    description: str
    thumbnail_url: HttpUrl | None = None


class ListingUpdate(BaseModel):
    title: str | None = Field(None, max_length=50)
    description: str | None = Field(None)
    price: float | None = Field(ge=0.0)
    category: Category | None
    condition: Condition | None
    thumbnail_url: HttpUrl | None
    is_active: bool


class ListingPublic(ListingBase):
    id: uuid
    seller_id: uuid
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
