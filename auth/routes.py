import os
from datetime import datetime, timezone

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
    ApiKeysResponse,
    AuthResponse,
    DeleteAccountResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthRequest,
    LoginRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignupRequest,
    UpdateApiKeysRequest
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


def mask_api_key(key: str | None) -> str | None:
    """
    Mask sensitive API keys for safe display to the client.
    Example: 'AIzaSy...4x8A' or '••••••••'
    """
    if not key:
        return None
    cleaned = key.strip()
    if len(cleaned) <= 8:
        return "••••••••"
    return f"{cleaned[:4]}••••••••{cleaned[-4:]}"


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

    if not user or not user.password_hash:

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
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url
    )


# =========================
# GOOGLE OAUTH
# =========================

@router.post(
    "/google",
    response_model=AuthResponse
)
def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            request.id_token,
            google_requests.Request(),
            audience=google_client_id if google_client_id else None
        )
    except Exception as verify_err:
        try:
            import httpx
            resp = httpx.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={request.id_token}",
                timeout=10.0
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google ID token."
                )
            idinfo = resp.json()
            if google_client_id and idinfo.get("aud") != google_client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google token audience mismatch."
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(verify_err)}"
            )

    email = idinfo.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account did not return a valid email address."
        )

    google_sub = idinfo.get("sub")
    name = idinfo.get("name")
    picture = idinfo.get("picture")

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user:
        if not user.google_id and google_sub:
            user.google_id = google_sub
        if not user.name and name:
            user.name = name
        if not user.avatar_url and picture:
            user.avatar_url = picture
        db.commit()
        db.refresh(user)
    else:
        user = User(
            email=email,
            password_hash=None,
            google_id=google_sub,
            auth_provider="google",
            name=name,
            avatar_url=picture
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        user.id
    )

    return AuthResponse(
        message="Google sign-in successful.",
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url
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

    if (
        datetime.now(timezone.utc)
        > user.reset_token_expires_at
    ):

        user.reset_token_hash = None

        user.reset_token_expires_at = None

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    try:

        new_password_hash = hash_password(
            request.new_password
        )

        user.password_hash = (
            new_password_hash
        )

        # Invalidate the reset token
        # at the same time as changing
        # the password.
        user.reset_token_hash = None

        user.reset_token_expires_at = None

        db.commit()

    except Exception:

        db.rollback()

        raise

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


# =========================
# API KEYS & BYOK
# =========================

@router.get(
    "/api-keys",
    response_model=ApiKeysResponse
)
def get_api_keys(
    current_user: User = Depends(
        get_current_user
    )
):
    return ApiKeysResponse(
        has_gemini_key=bool(current_user.gemini_api_key),
        gemini_key_masked=mask_api_key(current_user.gemini_api_key),
        has_groq_key=bool(current_user.groq_api_key),
        groq_key_masked=mask_api_key(current_user.groq_api_key),
        has_tavily_key=bool(current_user.tavily_api_key),
        tavily_key_masked=mask_api_key(current_user.tavily_api_key)
    )


@router.post(
    "/api-keys",
    response_model=ApiKeysResponse
)
def update_api_keys(
    request: UpdateApiKeysRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(
            User.id == current_user.id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    if request.gemini_api_key is not None:
        cleaned = request.gemini_api_key.strip()
        user.gemini_api_key = cleaned if cleaned else None

    if request.groq_api_key is not None:
        cleaned = request.groq_api_key.strip()
        user.groq_api_key = cleaned if cleaned else None

    if request.tavily_api_key is not None:
        cleaned = request.tavily_api_key.strip()
        user.tavily_api_key = cleaned if cleaned else None

    db.commit()
    db.refresh(user)

    return ApiKeysResponse(
        has_gemini_key=bool(user.gemini_api_key),
        gemini_key_masked=mask_api_key(user.gemini_api_key),
        has_groq_key=bool(user.groq_api_key),
        groq_key_masked=mask_api_key(user.groq_api_key),
        has_tavily_key=bool(user.tavily_api_key),
        tavily_key_masked=mask_api_key(user.tavily_api_key)
    )