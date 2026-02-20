"""
Test suite for API token management.
Covers: token CRUD, multi-user isolation, API authentication via tokens.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from beaverhabits.app.db import User, engine
from beaverhabits.main import app

PASSWORD = "TestPassword123!"

# 200 = has habits, 404 = auth OK but no habit_list yet — both mean authenticated
AUTHENTICATED_CODES = {200, 404}


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(name="client", scope="module")
async def client_fixture():
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
    await engine.dispose()


async def _register_and_login(client: TestClient, email: str) -> tuple[User, str]:
    """Register a user and return (User, access_token)."""
    resp = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 201
    user = User(**resp.json())

    resp = client.post(
        "/auth/login",
        data={"grant_type": "password", "username": email, "password": PASSWORD},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return user, token


@pytest.fixture
async def user_a(client: TestClient):
    email = f"token_user_a_{datetime.now().timestamp()}@test.com"
    user, token = await _register_and_login(client, email)
    yield {"user": user, "jwt": token, "headers": {"Authorization": f"Bearer {token}"}}
    # Cleanup: delete any API token created during test
    from beaverhabits.app.crud import delete_user_api_token
    await delete_user_api_token(user)


@pytest.fixture
async def user_b(client: TestClient):
    email = f"token_user_b_{datetime.now().timestamp()}@test.com"
    user, token = await _register_and_login(client, email)
    yield {"user": user, "jwt": token, "headers": {"Authorization": f"Bearer {token}"}}
    from beaverhabits.app.crud import delete_user_api_token
    await delete_user_api_token(user)


# ============================================================================
# CRUD via API: create habit → use API token to list
# ============================================================================


async def test_create_api_token(user_a, client: TestClient):
    """Test creating an API token via CRUD and using it for API auth."""
    from beaverhabits.app.crud import create_user_api_token, get_user_api_token

    user = user_a["user"]

    # Initially no token
    token = await get_user_api_token(user)
    assert token is None

    # Create token
    token = await create_user_api_token(user)
    assert token is not None
    assert len(token) > 20

    # Retrieve token
    retrieved = await get_user_api_token(user)
    assert retrieved == token


async def test_reset_api_token(user_a, client: TestClient):
    """Test resetting an API token produces a new value."""
    from beaverhabits.app.crud import (
        create_user_api_token,
        get_user_api_token,
        reset_user_api_token,
    )

    user = user_a["user"]
    original = await create_user_api_token(user)
    new_token = await reset_user_api_token(user)

    assert new_token != original
    assert await get_user_api_token(user) == new_token


async def test_delete_api_token(user_a, client: TestClient):
    """Test deleting an API token clears it."""
    from beaverhabits.app.crud import (
        create_user_api_token,
        delete_user_api_token,
        get_user_api_token,
    )

    user = user_a["user"]
    await create_user_api_token(user)
    await delete_user_api_token(user)

    assert await get_user_api_token(user) is None


# ============================================================================
# API authentication with API token
# ============================================================================


async def test_api_token_auth_lists_habits(user_a, client: TestClient):
    """Test that an API token can be used as Bearer token for API requests."""
    from beaverhabits.app.crud import create_user_api_token

    user = user_a["user"]
    api_token = await create_user_api_token(user)

    # Create a habit with JWT first
    resp = client.post(
        "/api/v1/habits",
        json={"name": "Token Test Habit"},
        headers=user_a["headers"],
    )
    assert resp.status_code == 200

    # List habits with API token
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {api_token}"},
    )
    assert resp.status_code == 200
    habits = resp.json()
    assert any(h["name"] == "Token Test Habit" for h in habits)


async def test_invalid_api_token_rejected(client: TestClient):
    """Test that a random string is rejected as Bearer token."""
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": "Bearer totally_invalid_token_xyz"},
    )
    assert resp.status_code == 401


async def test_deleted_token_rejected(user_a, client: TestClient):
    """Test that a deleted API token no longer authenticates."""
    from beaverhabits.app.crud import delete_user_api_token, reset_user_api_token

    user = user_a["user"]
    api_token = await reset_user_api_token(user)

    # Works before delete
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {api_token}"},
    )
    assert resp.status_code in AUTHENTICATED_CODES

    # Delete and verify rejection
    await delete_user_api_token(user)
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {api_token}"},
    )
    assert resp.status_code == 401


async def test_old_token_rejected_after_reset(user_a, client: TestClient):
    """Test that the old API token stops working after a reset."""
    from beaverhabits.app.crud import reset_user_api_token

    user = user_a["user"]
    old_token = await reset_user_api_token(user)
    new_token = await reset_user_api_token(user)

    # Old token rejected
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert resp.status_code == 401

    # New token works
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {new_token}"},
    )
    assert resp.status_code in AUTHENTICATED_CODES


# ============================================================================
# Multi-user isolation
# ============================================================================


async def test_tokens_are_unique_per_user(user_a, user_b, client: TestClient):
    """Test that two users get different API tokens."""
    from beaverhabits.app.crud import reset_user_api_token

    token_a = await reset_user_api_token(user_a["user"])
    token_b = await reset_user_api_token(user_b["user"])

    assert token_a != token_b


async def test_token_returns_correct_user(user_a, user_b, client: TestClient):
    """Test that get_user_by_api_token returns the right user for each token."""
    from beaverhabits.app.crud import get_user_by_api_token, reset_user_api_token

    token_a = await reset_user_api_token(user_a["user"])
    token_b = await reset_user_api_token(user_b["user"])

    resolved_a = await get_user_by_api_token(token_a)
    resolved_b = await get_user_by_api_token(token_b)

    assert resolved_a is not None
    assert resolved_b is not None
    assert str(resolved_a.id) == str(user_a["user"].id)
    assert str(resolved_b.id) == str(user_b["user"].id)


async def test_user_a_cannot_see_user_b_habits(user_a, user_b, client: TestClient):
    """Test that API tokens are isolated: user A's token cannot see user B's habits."""
    from beaverhabits.app.crud import reset_user_api_token

    token_a = await reset_user_api_token(user_a["user"])
    token_b = await reset_user_api_token(user_b["user"])

    # User A creates a habit
    resp = client.post(
        "/api/v1/habits",
        json={"name": "UserA Exclusive Habit"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200

    # User B creates a different habit
    resp = client.post(
        "/api/v1/habits",
        json={"name": "UserB Exclusive Habit"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200

    # User A should see their habit, not user B's
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    names_a = [h["name"] for h in resp.json()]
    assert "UserA Exclusive Habit" in names_a
    assert "UserB Exclusive Habit" not in names_a

    # User B should see their habit, not user A's
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 200
    names_b = [h["name"] for h in resp.json()]
    assert "UserB Exclusive Habit" in names_b
    assert "UserA Exclusive Habit" not in names_b


async def test_reset_one_user_does_not_affect_other(user_a, user_b, client: TestClient):
    """Test that resetting user A's token doesn't break user B's token."""
    from beaverhabits.app.crud import reset_user_api_token

    await reset_user_api_token(user_a["user"])
    token_b = await reset_user_api_token(user_b["user"])

    # Reset user A's token
    await reset_user_api_token(user_a["user"])

    # User B's token still works
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code in AUTHENTICATED_CODES


async def test_delete_one_user_does_not_affect_other(user_a, user_b, client: TestClient):
    """Test that deleting user A's token doesn't break user B's token."""
    from beaverhabits.app.crud import (
        delete_user_api_token,
        reset_user_api_token,
    )

    await reset_user_api_token(user_a["user"])
    token_b = await reset_user_api_token(user_b["user"])

    # Delete user A's token
    await delete_user_api_token(user_a["user"])

    # User B's token still works
    resp = client.get(
        "/api/v1/habits",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code in AUTHENTICATED_CODES
