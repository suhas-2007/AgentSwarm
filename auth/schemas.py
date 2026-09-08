from pydantic import BaseModel, EmailStr, Field


# =========================
# SIGNUP
# =========================

class SignupRequest(BaseModel):

    email: EmailStr = Field(
        ...,
        description="User email address."
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="User password."
    )


# =========================
# LOGIN
# =========================

class LoginRequest(BaseModel):

    email: EmailStr = Field(
        ...,
        description="User email address."
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=72,
        description="User password."
    )


class AuthResponse(BaseModel):

    message: str

    access_token: str

    token_type: str = "bearer"

    user_id: int

    email: EmailStr

    name: str | None = None

    avatar_url: str | None = None


# =========================
# GOOGLE OAUTH
# =========================

class GoogleAuthRequest(BaseModel):

    id_token: str = Field(
        ...,
        min_length=10,
        description="Google OAuth ID Token (JWT) from Google Identity Services."
    )


# =========================
# API KEYS & BYOK
# =========================

class ApiKeysResponse(BaseModel):

    has_gemini_key: bool
    gemini_key_masked: str | None = None

    has_groq_key: bool
    groq_key_masked: str | None = None

    has_tavily_key: bool
    tavily_key_masked: str | None = None


class UpdateApiKeysRequest(BaseModel):

    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    tavily_api_key: str | None = None


# =========================
# FORGOT PASSWORD
# =========================

class ForgotPasswordRequest(BaseModel):

    email: EmailStr = Field(
        ...,
        description="Email address associated with the account."
    )


class ForgotPasswordResponse(BaseModel):

    message: str


# =========================
# RESET PASSWORD
# =========================

class ResetPasswordRequest(BaseModel):

    token: str = Field(
        ...,
        min_length=1,
        description="Password reset token."
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="New account password."
    )


class ResetPasswordResponse(BaseModel):

    message: str


# =========================
# DELETE ACCOUNT
# =========================

class DeleteAccountResponse(BaseModel):

    message: str