import os
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user

from auth.schemas import (
    AuthResponse,
    DeleteAccountResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest
)

from auth.security import (
    create_access_token,
    generate_reset_token,
    get_reset_token_expiry,
    hash_password,
    hash_reset_token,
    verify_password
)

from database.connection import get_db
from database.models import User

from services.email_service import (
    send_password_reset_email
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================
# SIGNUP
# =========================

@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.scalar(
        select(User).where(
            User.email == request.email
        )
    )

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            )
        )

    password_hash = hash_password(
        request.password
    )

    user = User(
        email=request.email,
        password_hash=password_hash
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    access_token = create_access_token(
        user.id
    )

    return AuthResponse(
        message="Account created successfully.",
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )


# =========================
# LOGIN
# =========================

@router.post(
    "/login",
    response_model=AuthResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.email == request.email
        )
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(
        request.password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        user.id
    )

    return AuthResponse(
        message="Login successful.",
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )


# =========================
# FORGOT PASSWORD
# =========================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.email == request.email
        )
    )

    if user:

        reset_token = generate_reset_token()

        user.reset_token_hash = (
            hash_reset_token(reset_token)
        )

        user.reset_token_expires_at = (
            get_reset_token_expiry()
        )

        db.commit()


        frontend_url = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        ).rstrip("/")


        reset_link = (
            f"{frontend_url}"
            f"/reset-password?token="
            f"{reset_token}"
        )


        try:

            send_password_reset_email(
                recipient_email=user.email,
                reset_link=reset_link
            )

            print(
                f"Password reset email sent to "
                f"{user.email}"
            )

        except Exception as exc:

            print(
                "PASSWORD RESET EMAIL ERROR:"
            )

            print(str(exc))


    return ForgotPasswordResponse(
        message=(
            "If an account exists with this email, "
            "password reset instructions have been sent."
        )
    )


# =========================
# RESET PASSWORD
# =========================

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    token_hash = hash_reset_token(
        request.token
    )

    user = db.scalar(
        select(User).where(
            User.reset_token_hash == token_hash
        )
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if not user.reset_token_expires_at:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if datetime.utcnow() > user.reset_token_expires_at:

        user.reset_token_hash = None

        user.reset_token_expires_at = None

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    user.password_hash = hash_password(
        request.new_password
    )

    user.reset_token_hash = None

    user.reset_token_expires_at = None

    db.commit()

    return ResetPasswordResponse(
        message="Password reset successfully."
    )


# =========================
# DELETE ACCOUNT
# =========================

@router.delete(
    "/account",
    response_model=DeleteAccountResponse
)
def delete_account(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    db.delete(current_user)

    db.commit()

    return DeleteAccountResponse(
        message="Account deleted successfully."
    )