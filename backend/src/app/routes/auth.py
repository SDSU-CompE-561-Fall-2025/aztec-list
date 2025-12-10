from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.core.settings import Settings, get_settings
from app.models.user import User
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
    response_model=UserPublic,
)
@limiter.limit("2/minute;5/hour")
async def signup(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Register a new user account.

    Rate limit: 2 per minute (burst), 5 per hour (sustained) to prevent spam accounts.

    Args:
        request: FastAPI request object (required for rate limiting)
        user: User registration data (username, email, password)
        db: Database session

    Returns:
        UserPublic: Created user's public information

    Raises:
        HTTPException: 400 if email already exists, 429 if rate limit exceeded
    """
    return user_service.create(db, user)


@auth_router.post("/login", summary="Authenticate and obtain a JWT access token")
@limiter.limit("3/minute;10/hour")
async def login(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """
    Authenticate user and return access token.

    OAuth2 compatible token login - username field accepts email or username.

    Rate limit: 3 per minute (burst), 10 per hour (sustained) to prevent brute force attacks.

    Args:
        request: FastAPI request object (required for rate limiting)
        form_data: OAuth2 form with username (email or username) and password
        db: Database session
        settings: Application settings

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid, 403 if account is banned, 429 if rate limit exceeded
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
