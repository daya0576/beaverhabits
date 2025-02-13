# Beaver Habits API Documentation

This document describes the available API endpoints for the Beaver Habits application.

## Authentication

All API endpoints require authentication using email and password. These credentials must be provided in the request body.

## Available Endpoints

### Lists API

- **Endpoint**: `/api/v1/lists`
- **Method**: POST
- **Description**: Get all lists for the authenticated user
- **Authentication**: Requires email and password
- **Example Usage**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/lists \
    -H "Content-Type: application/json" \
    -d '{
      "email": "your.email@example.com",
      "password": "your_password"
    }'
  ```
- **Response Format**:
  ```json
  {
    "lists": [
      {
        "id": "list_id",
        "name": "List Name"
      }
    ]
  }
  ```

### Single Habit Update API

- **Endpoint**: `/api/v1/habits/{habit_id}/completions`
- **Method**: POST
- **Description**: Update completion status for a single habit
- **Authentication**: Requires email and password
- **Example Usage**:

  ```bash
  # Mark a habit as completed
  curl -X POST http://localhost:8000/api/v1/habits/habit123/completions \
    -H "Content-Type: application/json" \
    -d '{
      "date": "2025-02-13",
      "done": true
    }'

  # Mark a habit as not completed
  curl -X POST http://localhost:8000/api/v1/habits/habit123/completions \
    -H "Content-Type: application/json" \
    -d '{
      "date": "2025-02-13",
      "done": false
    }'

  # Mark a habit as skipped
  curl -X POST http://localhost:8000/api/v1/habits/habit123/completions \
    -H "Content-Type: application/json" \
    -d '{
      "date": "2025-02-13",
      "done": null
    }'
  ```

- **Response Format**:
  ```json
  {
    "day": "13-02-2025",
    "done": true // or false, or null for skipped
  }
  ```
- **Notes**:
  - The `done` field can be:
    - `true`: Habit is completed
    - `false`: Habit is not completed
    - `null`: Habit is skipped
  - Returns 401 for invalid credentials
  - Returns 404 if habit not found
  - Returns 400 for invalid date format

### Batch Update Habits API

- **Endpoint**: `/api/v1/habits/batch-completions`
- **Method**: POST
- **Description**: Update multiple completion statuses for a habit at once
- **Authentication**: Requires email and password
- **Example Usage**:

  ```bash
  # Mark habits as completed or not completed
  curl -X POST http://localhost:8000/api/v1/habits/batch-completions \
    -H "Content-Type: application/json" \
    -d '{
      "email": "your.email@example.com",
      "password": "your_password",
      "habit_id": "habit123",
      "completions": [
        {
          "date": "2025-02-13",
          "done": true
        },
        {
          "date": "2025-02-12",
          "done": false
        }
      ]
    }'

  # Mark habits as skipped
  curl -X POST http://localhost:8000/api/v1/habits/batch-completions \
    -H "Content-Type: application/json" \
    -d '{
      "email": "your.email@example.com",
      "password": "your_password",
      "habit_id": "habit123",
      "completions": [
        {
          "date": "2025-02-13",
          "done": null
        }
      ]
    }'
  ```

- **Response Format**:
  ```json
  {
    "habit_id": "habit123",
    "updated": [
      {
        "date": "2025-02-13",
        "done": true
      },
      {
        "date": "2025-02-12",
        "done": false
      }
    ]
  }
  ```
- **Notes**:
  - Dates should be in ISO format (YYYY-MM-DD)
  - All updates are processed in order
  - If any date fails to update, the request is aborted
  - The `done` field can be:
    - `true`: Habit is completed
    - `false`: Habit is not completed
    - `null`: Habit is skipped
  - Returns 401 for invalid credentials
  - Returns 404 if habit not found
  - Returns 400 for invalid date formats

### Export Habits API

- **Endpoint**: `/api/v1/export/habits`
- **Method**: POST
- **Description**: Retrieve habit information for the last 30 days in JSON format
- **Authentication**: Requires email and password
- **Parameters**:
  - `email`: User's email address (required)
  - `password`: User's password (required)
  - `list_id`: Filter habits by list ID (optional)
  - `archive`: Include archived habits (optional, default: false)
- **Example Usage**:

  ```bash
  # Get active habits from a specific list
  curl -X POST http://localhost:8000/api/v1/export/habits \
    -H "Content-Type: application/json" \
    -d '{
      "email": "your.email@example.com",
      "password": "your_password",
      "list_id": "specific_list_id"
    }'

  # Get both active and archived habits
  curl -X POST http://localhost:8000/api/v1/export/habits \
    -H "Content-Type: application/json" \
    -d '{
      "email": "your.email@example.com",
      "password": "your_password",
      "archive": true
    }'
  ```

- **Response Format**:
  ```json
  {
    "habits": [
      {
        "id": "habit_id",
        "name": "Habit Name",
        "star": true,
        "status": "active",
        "weekly_goal": 5,
        "records": {
          "2025-02-13": {
            "done": true,
            "text": "Optional note"
          }
        }
      }
    ],
    "order": ["habit_id1", "habit_id2"],
    "date_range": {
      "start": "2025-01-14",
      "end": "2025-02-13"
    }
  }
  ```
- **Notes**:
  - By default, only returns active habits
  - Set `archive: true` to include both active and archived habits
  - Use `list_id` to filter habits by a specific list
  - Soft-deleted habits are never included
