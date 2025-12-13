from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.core.email import email_service
from app.core.rate_limiter import limiter
from app.core.security import generate_verification_token, get_verification_token_expiry
from app.core.settings import Settings, get_settings
from app.repository.user import UserRepository
from app.schemas.user import Token, UserCreate, UserPrivate, UserPublicWithEmailStatus
from app.services.user import user_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth_router.post(
    "/signup",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublicWithEmailStatus,
)
@limiter.limit("2/minute;5/hour")
async def signup(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    user: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Register a new user account.

    Rate limit: 2 per minute (burst), 5 per hour (sustained) to prevent spam accounts.

    Args:
        request: FastAPI request object (required for rate limiting)
        user: User registration data (username, email, password)
        db: Database session

    Returns:
        UserPublicWithEmailStatus: Created user's public information with email sending status

    Raises:
        HTTPException: 400 if email already exists, 429 if rate limit exceeded
    """
    db_user, email_sent = user_service.create(db, user)
    return {
        **UserPrivate.model_validate(db_user).model_dump(),
        "verification_email_sent": email_sent,
    }


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
        user=UserPrivate.model_validate(user),
    )


@auth_router.post(
    "/verify-email",
    summary="Verify user email address",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def verify_email(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """
    Verify user email address using token from email.

    Rate limit: 5 per minute to prevent token bruteforce.

    Args:
        request: FastAPI request object (required for rate limiting)
        token: Verification token from email link
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: 400 if token is invalid or expired, 429 if rate limit exceeded
    """
    user = UserRepository.get_by_verification_token(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    UserRepository.mark_as_verified(db, user)

    return {"message": "Email verified successfully"}


@auth_router.post(
    "/resend-verification",
    summary="Resend verification email",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,  # noqa: ARG001 - Required by slowapi for rate limiting
    email: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """
    Resend verification email to user.

    Rate limit: 3 per hour to prevent email spam.

    Args:
        request: FastAPI request object (required for rate limiting)
        email: User's email address
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: 400 if user not found or already verified, 429 if rate limit exceeded
    """
    user = UserRepository.get_by_email(db, email)

    if not user:
        # Don't reveal if email exists for security
        return {"message": "If that email exists, a verification link has been sent"}

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    # Generate new verification token
    verification_token = generate_verification_token()
    expiry = get_verification_token_expiry()
    UserRepository.set_verification_token(db, user, verification_token, expiry)

    # Send verification email
    email_service.send_email_verification(
        email=user.email,
        username=user.username,
        verification_token=verification_token,
    )

    return {"message": "Verification email sent"}
