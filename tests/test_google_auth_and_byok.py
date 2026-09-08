from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import select
from database.models import User


def test_google_auth_creates_new_user_without_password(client, db_session):
    mock_idinfo = {
        "sub": "google-user-123",
        "email": "google.test.user@example.com",
        "name": "Google Test User",
        "picture": "https://example.com/avatar.png"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
        response = client.post(
            "/auth/google",
            json={"id_token": "mock.google.id.token.xyz123"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Google sign-in successful."
    assert "access_token" in data
    assert data["email"] == "google.test.user@example.com"
    assert data["name"] == "Google Test User"
    assert data["avatar_url"] == "https://example.com/avatar.png"

    # Verify user record in database
    user = db_session.scalar(
        select(User).where(User.email == "google.test.user@example.com")
    )
    assert user is not None
    assert user.password_hash is None
    assert user.google_id == "google-user-123"
    assert user.auth_provider == "google"


def test_google_user_cannot_login_with_password(client, db_session):
    # Try logging in with a password for a pure Google account
    response = client.post(
        "/auth/login",
        json={
            "email": "google.test.user@example.com",
            "password": "Password123!"
        }
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_google_auth_links_existing_user(client, test_user, db_session):
    mock_idinfo = {
        "sub": "google-linked-456",
        "email": test_user.email,
        "name": "Linked Test User",
        "picture": "https://example.com/linked.png"
    }

    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_idinfo):
        response = client.post(
            "/auth/google",
            json={"id_token": "mock.google.id.token.existing"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["email"] == test_user.email

    db_session.refresh(test_user)
    assert test_user.google_id == "google-linked-456"
    assert test_user.password_hash == "test-password"  # Password remains untouched


def test_api_keys_get_masks_secrets(client, test_user, db_session):
    test_user.gemini_api_key = "AIzaSyGeminiSecretKey987654"
    test_user.groq_api_key = "gsk_GroqSecretKey12345678"
    test_user.tavily_api_key = "tvly-TavilySecretKey0000"
    db_session.commit()

    response = client.get("/auth/api-keys")
    assert response.status_code == 200
    data = response.json()

    assert data["has_gemini_key"] is True
    assert data["has_groq_key"] is True
    assert data["has_tavily_key"] is True

    # Check masking
    assert data["gemini_key_masked"] == "AIza••••••••7654"
    assert data["groq_key_masked"] == "gsk_••••••••5678"
    assert data["tavily_key_masked"] == "tvly••••••••0000"

    # Verify raw secrets are never leaked
    assert "GeminiSecretKey" not in response.text
    assert "GroqSecretKey" not in response.text
    assert "TavilySecretKey" not in response.text


def test_api_keys_post_updates_and_clears_keys(client, test_user, db_session):
    response = client.post(
        "/auth/api-keys",
        json={
            "gemini_api_key": "AIzaNewCustomKey112233",
            "groq_api_key": "gsk_NewCustomGroq445566",
            "tavily_api_key": "tvly-NewCustomTavily778899"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_gemini_key"] is True
    assert data["has_groq_key"] is True
    assert data["has_tavily_key"] is True

    db_session.expire_all()
    db_user = db_session.scalar(select(User).where(User.id == test_user.id))
    assert db_user.gemini_api_key == "AIzaNewCustomKey112233"
    assert db_user.groq_api_key == "gsk_NewCustomGroq445566"
    assert db_user.tavily_api_key == "tvly-NewCustomTavily778899"

    # Test clearing keys with empty strings
    clear_response = client.post(
        "/auth/api-keys",
        json={
            "gemini_api_key": "",
            "groq_api_key": "",
            "tavily_api_key": ""
        }
    )
    assert clear_response.status_code == 200
    clear_data = clear_response.json()
    assert clear_data["has_gemini_key"] is False
    assert clear_data["has_groq_key"] is False
    assert clear_data["has_tavily_key"] is False

    db_session.expire_all()
    db_user = db_session.scalar(select(User).where(User.id == test_user.id))
    assert db_user.gemini_api_key is None
    assert db_user.groq_api_key is None
    assert db_user.tavily_api_key is None


def test_planner_agent_uses_custom_api_key():
    from agents.planner import get_llm

    with patch("agents.planner.ChatGroq") as mock_groq:
        get_llm(api_key="custom-groq-key")
        mock_groq.assert_called_once_with(
            model="openai/gpt-oss-120b",
            api_key="custom-groq-key",
            temperature=0
        )


def test_evaluator_agent_uses_custom_api_key():
    from agents.evaluator import get_llm

    with patch("agents.evaluator.ChatGoogleGenerativeAI") as mock_gemini:
        get_llm(api_key="custom-gemini-key")
        mock_gemini.assert_called_once_with(
            model="gemini-3.6-flash",
            google_api_key="custom-gemini-key",
            temperature=0
        )


def test_web_search_uses_custom_api_key():
    from tools.web_search import web_search

    with patch("tools.web_search.get_tavily_client") as mock_get_client:
        mock_client_instance = MagicMock()
        mock_client_instance.search.return_value = {"results": []}
        mock_get_client.return_value = mock_client_instance

        web_search("test query", api_key="custom-tavily-key")

        mock_get_client.assert_called_once_with("custom-tavily-key")
        mock_client_instance.search.assert_called_once()
