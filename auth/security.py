import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt


load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured."
    )


ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

RESET_TOKEN_EXPIRE_MINUTES = 15


def hash_password(password: str) -> str:

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError(
            "Password cannot be longer than 72 bytes."
        )

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password_bytes,
        salt
    )

    return hashed_password.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    return bcrypt.checkpw(
        password_bytes,
        hashed_bytes
    )


def create_access_token(user_id: int) -> str:

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> int:

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        subject = payload.get("sub")

        if subject is None:
            raise ValueError(
                "Token does not contain a user ID."
            )

        return int(subject)

    except (
        JWTError,
        ValueError,
        TypeError
    ) as exc:

        raise ValueError(
            "Invalid or expired access token."
        ) from exc


def generate_reset_token() -> str:

    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def get_reset_token_expiry() -> datetime:

    return (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )
    )