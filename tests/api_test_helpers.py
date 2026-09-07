from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.api as api_module

from auth.dependencies import get_current_user
from database.connection import Base, get_db
from database.models import User


engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


Base.metadata.create_all(
    bind=engine
)


def override_get_db():

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


def get_or_create_test_user():

    db = TestingSessionLocal()

    try:

        user = db.query(User).filter(
            User.email == "test@example.com"
        ).first()

        if user is None:

            user = User(
                email="test@example.com",
                password_hash="test-password"
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    finally:

        db.close()


def override_get_current_user():

    return get_or_create_test_user()


api_module.app.dependency_overrides[
    get_db
] = override_get_db


api_module.app.dependency_overrides[
    get_current_user
] = override_get_current_user
