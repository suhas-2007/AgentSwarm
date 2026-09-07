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