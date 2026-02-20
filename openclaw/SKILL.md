---
name: beaverhabits
description: Track and manage your habits using the Beaver Habit Tracker API.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - BEAVERHABITS_API_KEY
      bins:
        - curl
    primaryEnv: BEAVERHABITS_API_KEY
    emoji: "\U0001F9AB"
    homepage: https://github.com/daya0576/beaverhabits
---

# Beaver Habit Tracker

Track and manage your daily habits using the [Beaver Habit Tracker](https://beaverhabits.com) API.

## Setup

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BEAVERHABITS_API_KEY` | Yes | — | Your permanent API token from the Beaver Habits settings page |
| `SERVER_URL` | No | `https://beaverhabits.com` | Your Beaver Habits server URL (for self-hosted instances) |

### Getting Your API Key

1. Log in to your Beaver Habits instance
2. Open the menu → Tools → API Tokens
3. Click "Generate API Token"
4. Copy the token and set it as `BEAVERHABITS_API_KEY`

## Tools

### list_habits

List all active habits.

```bash
curl -s -H "Authorization: Bearer $BEAVERHABITS_API_KEY" \
  "${SERVER_URL:-https://beaverhabits.com}/api/v1/habits"
```

**Response:**

```json
[
  {"id": "f41e44", "name": "Running"},
  {"id": "87e537", "name": "Reading"}
]
```

### complete_habit

Mark a habit as done (or undone) for a specific date.

**Parameters:**
- `habit_id` (resolved): Automatically resolved by calling `list_habits` and matching the user's habit name. Never ask the user for this value.
- `date` (required): Date in DD-MM-YYYY format
- `done` (optional): `true` to complete, `false` to uncomplete (default: `true`)

```bash
curl -s -X POST \
  -H "Authorization: Bearer $BEAVERHABITS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"date": "20-02-2026", "done": true, "date_fmt": "%d-%m-%Y"}' \
  "${SERVER_URL:-https://beaverhabits.com}/api/v1/habits/{habit_id}/completions"
```

**Response:**

```json
{"day": "20-02-2026", "done": true}
```

### get_completions

Show recent habit completions for a given habit.

**Parameters:**
- `habit_id` (resolved): Automatically resolved by calling `list_habits` and matching the user's habit name. Never ask the user for this value.
- `date_start` (optional): Start date in DD-MM-YYYY format
- `date_end` (optional): End date in DD-MM-YYYY format
- `limit` (optional): Max number of results (default: 10)
- `sort` (optional): `asc` or `desc` (default: `asc`)

```bash
curl -s -H "Authorization: Bearer $BEAVERHABITS_API_KEY" \
  "${SERVER_URL:-https://beaverhabits.com}/api/v1/habits/{habit_id}/completions?date_fmt=%25d-%25m-%25Y&sort=desc&limit=10"
```

**Response:**

```json
["20-02-2026", "19-02-2026", "18-02-2026"]
```

## Usage Instructions

- **Always call `list_habits` first** before any other tool to resolve habit names to IDs. The user will refer to habits by name — never ask them for a `habit_id`.
- When completing a habit, always use today's date unless the user specifies otherwise. Use `date_fmt=%d-%m-%Y` format.
- When showing completions, default to the last 10 entries sorted descending (most recent first) unless the user asks differently.
- If multiple habits match the user's input, ask the user to clarify which one they mean.
- Always confirm the action taken (e.g., "Marked 'Running' as done for today").
