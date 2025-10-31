from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.core.settings import Settings, get_settings
from app.schemas.user import Token, UserCreate, UserPublic
from app.services.user import user_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth_router.post(
    "/signup",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserPublic:
    """
    Register a new user account.

    Args:
        user: User registration data (username, email, password)
        db: Database session

    Returns:
        UserPublic: Created user's public information

    Raises:
        HTTPException: 400 if email already exists, 500 on database error
    """
    created_user = user_service.create(db, user)
    return UserPublic.model_validate(created_user)


@auth_router.post("/login", summary="Authenticate and obtain a JWT access token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """
    Authenticate user and return access token.

    OAuth2 compatible token login - username field accepts email or username.

    Args:
        form_data: OAuth2 form with username (email or username) and password
        db: Database session
        settings: Application settings

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid, 403 if account is banned
    """
    # Service handles authentication, credential validation, and ban check
    user = user_service.authenticate(db, form_data.username, form_data.password)

    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",  # noqa: S106
        user=UserPublic.model_validate(user),
    )
