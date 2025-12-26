"""
Test suite for Beaver Habits API based on the official API documentation.
Tests cover: authentication, habit CRUD operations, and habit completions.
"""

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from loguru import logger
from nicegui import core

from beaverhabits.app.db import User, engine
from beaverhabits.main import app

PASSWORD = "TestPassword123!"


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================


@pytest.fixture(name="client", scope="module")
async def client_fixture():
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client

    await engine.dispose()


@pytest.fixture
async def test_user(client: TestClient):
    """Set up the database before tests and tear down after."""
    logger.info("Registering test user...")
    email = f"testuser_{datetime.now().timestamp()}@test.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    user_data = response.json()
    user = User(**user_data)

    yield user


@pytest.fixture
async def access_token(test_user: User, client: TestClient):
    """Obtain an access token for the test user (Task 1 from docs)."""
    logger.info(f"Obtaining access token for user: {test_user.email}")
    response = client.post(
        "/auth/login",
        data={
            "grant_type": "password",
            "username": test_user.email,
            "password": PASSWORD,
        },
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "accept": "application/json",
        },
    )
    logger.info(f"Access token response: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    return data["access_token"]


@pytest.fixture
async def auth_headers(access_token):
    """Get authorization headers with access token."""
    return {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json",
    }


@pytest.fixture
async def sample_habit(auth_headers, client: TestClient):
    """Create a sample habit for testing."""
    response = client.post(
        "/api/v1/habits",
        json={"name": "Test Habit"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    return response.json()


# ============================================================================
# Task 1 - Authentication Tests
# ============================================================================


async def test_create_user(client: TestClient):
    """Test user registration."""
    email = f"newuser_{datetime.now().timestamp()}@test.com"
    data = {"email": email, "password": PASSWORD}
    response = client.post("/auth/register", json=data)

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert response.json()["is_active"] == True


async def test_obtain_access_token(test_user, client: TestClient):
    """
    Task 1 - Obtain an Access Token
    Test authentication with username and password.
    """
    response = client.post(
        "/auth/login",
        data={
            "grant_type": "password",
            "username": test_user.email,
            "password": PASSWORD,
        },
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


async def test_authentication_with_invalid_credentials(client: TestClient):
    """Test authentication fails with wrong credentials."""
    response = client.post(
        "/auth/login",
        data={
            "grant_type": "password",
            "username": "nonexistent@test.com",
            "password": "wrongpassword",
        },
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 400


async def test_api_without_token(client: TestClient):
    """Test that API endpoints require authentication."""
    response = client.get("/api/v1/habits")
    assert response.status_code == 401


# ============================================================================
# Task 2 - List Habits Tests
# ============================================================================


async def test_list_all_habits_empty(auth_headers, client: TestClient):
    """
    Task 2 - List All the Habits
    Test listing habits when no habits exist.
    """
    response = client.get(
        "/api/v1/habits",
        headers=auth_headers,
    )

    # New users might have no habits or return 404
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert isinstance(response.json(), list)


async def test_list_all_habits(auth_headers, client: TestClient):
    """
    Task 2 - List All the Habits
    Test listing habits with created habits.
    """
    logger.info(
        f"nicegui loop: {core.loop}, is_running: {core.loop and core.loop.is_running}"
    )

    # Create some test habits
    habit1 = client.post(
        "/api/v1/habits",
        json={"name": "Order pizza"},
        headers=auth_headers,
    )
    logger.info(f"Created habit1: {habit1.json()}")
    habit2 = client.post(
        "/api/v1/habits",
        json={"name": "Running"},
        headers=auth_headers,
    )
    logger.info(f"Created habit2: {habit2.json()}")

    # List all habits
    response = client.get(
        "/api/v1/habits",
        headers=auth_headers,
    )

    assert response.status_code == 200
    habits = response.json()
    assert isinstance(habits, list)
    assert len(habits) >= 2

    # Check structure
    for habit in habits:
        assert "id" in habit
        assert "name" in habit


def test_list_habits_filter_by_status(auth_headers, sample_habit, client: TestClient):
    """Test filtering habits by status (active/archived)."""
    # Test with active status
    response = client.get(
        "/api/v1/habits?status=active",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Archive the habit
    client.put(
        f"/api/v1/habits/{sample_habit['id']}",
        json={"status": "archive"},
        headers=auth_headers,
    )

    # Test with archived status
    response = client.get(
        "/api/v1/habits?status=archive",
        headers=auth_headers,
    )
    assert response.status_code == 200


# ============================================================================
# Habit CRUD Tests
# ============================================================================


def test_create_habit(auth_headers, client: TestClient):
    """Test creating a new habit."""
    response = client.post(
        "/api/v1/habits",
        json={"name": "Morning Exercise"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Morning Exercise"


def test_get_habit_detail(auth_headers, sample_habit, client: TestClient):
    """Test getting detailed information about a specific habit."""
    response = client.get(
        f"/api/v1/habits/{sample_habit['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_habit["id"]
    assert data["name"] == sample_habit["name"]
    assert "star" in data
    assert "records" in data
    assert "status" in data
    assert "tags" in data


def test_update_habit(auth_headers, sample_habit, client: TestClient):
    """Test updating habit properties."""
    response = client.put(
        f"/api/v1/habits/{sample_habit['id']}",
        json={
            "name": "Updated Habit Name",
            "star": True,
            "tags": ["health", "fitness"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Habit Name"
    assert data["star"] == True
    assert "health" in data["tags"]


def test_update_habit_period(auth_headers, sample_habit, client: TestClient):
    """Test updating habit frequency/period."""
    response = client.put(
        f"/api/v1/habits/{sample_habit['id']}",
        json={"period": {"period_type": "W", "period_count": 1, "target_count": 3}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["period"] is not None
    assert data["period"]["period_type"] == "W"
    assert data["period"]["target_count"] == 3


def test_delete_habit(auth_headers, sample_habit, client: TestClient):
    """Test deleting a habit."""
    response = client.delete(
        f"/api/v1/habits/{sample_habit['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Verify habit is deleted
    get_response = client.get(
        f"/api/v1/habits/{sample_habit['id']}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


# ============================================================================
# Task 3 - Complete Habit Tests
# ============================================================================


def test_complete_habit(auth_headers, sample_habit, client: TestClient):
    """
    Task 3 - Complete Habit
    Test marking a habit as completed for a specific date.
    """
    today = date.today()
    date_str = today.strftime("%d-%m-%Y")

    response = client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={"date_fmt": "%d-%m-%Y", "date": date_str, "done": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["day"] == date_str
    assert data["done"] == True


def test_uncomplete_habit(auth_headers, sample_habit, client: TestClient):
    """Test marking a habit as not completed (undoing completion)."""
    today = date.today()
    date_str = today.strftime("%d-%m-%Y")

    # First complete it
    client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={"date_fmt": "%d-%m-%Y", "date": date_str, "done": True},
        headers=auth_headers,
    )

    # Then uncomplete it
    response = client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={"date_fmt": "%d-%m-%Y", "date": date_str, "done": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["done"] == False


def test_complete_habit_with_note(auth_headers, sample_habit, client: TestClient):
    """Test completing a habit with a text note."""
    today = date.today()
    date_str = today.strftime("%d-%m-%Y")

    response = client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={
            "date_fmt": "%d-%m-%Y",
            "date": date_str,
            "done": True,
            "text": "Completed 30 minutes of running",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_complete_habit_invalid_date_format(
    auth_headers, sample_habit, client: TestClient
):
    """Test that invalid date format returns an error."""
    response = client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={
            "date_fmt": "%d-%m-%Y",
            "date": "2024-12-16",  # Wrong format (YYYY-MM-DD instead of DD-MM-YYYY)
            "done": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 400


# ============================================================================
# Task 4 - Show Recent Completions Tests
# ============================================================================


def test_show_recent_completions(auth_headers, sample_habit, client: TestClient):
    """
    Task 4 - Show Recent Habit Completions
    Test retrieving completion history for a habit.
    """
    # Complete the habit on multiple dates
    dates_to_complete = [
        date(2024, 12, 10),
        date(2024, 12, 12),
        date(2024, 12, 16),
    ]

    for completion_date in dates_to_complete:
        client.post(
            f"/api/v1/habits/{sample_habit['id']}/completions",
            json={
                "date_fmt": "%d-%m-%Y",
                "date": completion_date.strftime("%d-%m-%Y"),
                "done": True,
            },
            headers=auth_headers,
        )

    # Get completions for December 2024
    response = client.get(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        params={
            "date_fmt": "%d-%m-%Y",
            "date_start": "01-12-2024",
            "date_end": "30-12-2024",
            "status": "PERIOD_DONE,DONE",
            "sort": "asc",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    completions = response.json()
    assert isinstance(completions, list)
    assert len(completions) >= 3
    assert "10-12-2024" in completions
    assert "12-12-2024" in completions
    assert "16-12-2024" in completions


def test_completions_sorted_descending(auth_headers, sample_habit, client: TestClient):
    """Test that completions can be sorted in descending order."""
    # Complete on two dates
    client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={"date_fmt": "%d-%m-%Y", "date": "10-12-2024", "done": True},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        json={"date_fmt": "%d-%m-%Y", "date": "20-12-2024", "done": True},
        headers=auth_headers,
    )

    # Get with descending sort
    response = client.get(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        params={
            "date_fmt": "%d-%m-%Y",
            "date_start": "01-12-2024",
            "date_end": "31-12-2024",
            "sort": "desc",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    completions = response.json()
    # First item should be more recent than last item
    if len(completions) >= 2:
        first = datetime.strptime(completions[0], "%d-%m-%Y")
        last = datetime.strptime(completions[-1], "%d-%m-%Y")
        assert first >= last


def test_completions_with_limit(auth_headers, sample_habit, client: TestClient):
    """Test limiting the number of returned completions."""
    # Complete on multiple dates
    for day in range(1, 11):  # 10 completions
        client.post(
            f"/api/v1/habits/{sample_habit['id']}/completions",
            json={"date_fmt": "%d-%m-%Y", "date": f"{day:02d}-12-2024", "done": True},
            headers=auth_headers,
        )

    # Request with limit
    response = client.get(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        params={
            "date_fmt": "%d-%m-%Y",
            "date_start": "01-12-2024",
            "date_end": "31-12-2024",
            "limit": 5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    completions = response.json()
    assert len(completions) <= 5


def test_completions_date_range_validation(
    auth_headers, sample_habit, client: TestClient
):
    """Test that date range validation works correctly."""
    # Missing date_end
    response = client.get(
        f"/api/v1/habits/{sample_habit['id']}/completions",
        params={
            "date_fmt": "%d-%m-%Y",
            "date_start": "01-12-2024",
        },
        headers=auth_headers,
    )

    assert response.status_code == 400


# ============================================================================
# Additional Edge Cases
# ============================================================================


def test_get_nonexistent_habit(auth_headers, client: TestClient):
    """Test accessing a habit that doesn't exist."""
    response = client.get(
        "/api/v1/habits/nonexistent123",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_complete_nonexistent_habit(auth_headers, client: TestClient):
    """Test completing a habit that doesn't exist."""
    response = client.post(
        "/api/v1/habits/nonexistent123/completions",
        json={"date_fmt": "%d-%m-%Y", "date": "16-12-2024", "done": True},
        headers=auth_headers,
    )
    assert response.status_code == 404
