import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import api.api as api_module

from auth.dependencies import get_current_user
from database.connection import Base, get_db
from database.models import User


# ============================================================
# TEST DATABASE
# ============================================================

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


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture
def db_session():

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# TEST USER
# ============================================================

@pytest.fixture
def test_user(
    db_session
):

    user = (
        db_session.query(User)
        .filter(
            User.email == "test@example.com"
        )
        .first()
    )

    if user is None:

        user = User(
            email="test@example.com",
            password_hash="test-password"
        )

        db_session.add(user)

        db_session.commit()

        db_session.refresh(user)

    return user


# ============================================================
# SHARED DEPENDENCY OVERRIDES
# ============================================================

@pytest.fixture(autouse=True)
def override_dependencies(
    test_user
):

    def override_get_db():

        db = TestingSessionLocal()

        try:
            yield db

        finally:
            db.close()


    def override_get_current_user():

        return test_user


    api_module.app.dependency_overrides[
        get_db
    ] = override_get_db

    api_module.app.dependency_overrides[
        get_current_user
    ] = override_get_current_user


    yield


    api_module.app.dependency_overrides.clear()


# ============================================================
# FASTAPI TEST CLIENT
# ============================================================

@pytest.fixture
def client():

    with TestClient(
        api_module.app
    ) as test_client:

        yield test_client