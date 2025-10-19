from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.core.settings import settings
from app.schemas.user import Token, UserCreate, UserPublic
from app.services.user import user_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
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
    return user_service.create(db, user)


@auth_router.post("/login")
async def login(
    username: Annotated[str, Form(description="Email or username")],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Authenticate user and return access token.

    OAuth2 compatible token login - accepts email or username.

    Args:
        username: User email or username
        password: User password
        db: Database session

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = user_service.authenticate(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.a2.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.email)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")  # noqa: S106
