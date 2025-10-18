from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    display_name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema for user response."""

    display_name: str | None = None
    email: EmailStr | None = None
    is_verified: bool | None = None


class UserPublic(UserBase):
    id: int
    display_name: str
    is_verfied: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str
