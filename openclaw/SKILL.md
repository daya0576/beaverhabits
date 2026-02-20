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

API documentation: [https://beaverhabits.com/docs](https://beaverhabits.com/docs)

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

### list_habits (overview)

List all habits and show a weekly ASCII overview. This is the **default response** for any habit-related query.

**Step 1** — Get all habits:

```bash
curl -s -H "Authorization: Bearer $BEAVERHABITS_API_KEY" \
  "${SERVER_URL:-https://beaverhabits.com}/api/v1/habits"
```

**Step 2** — For each habit, get completions over the last 5 days:

```bash
curl -s -H "Authorization: Bearer $BEAVERHABITS_API_KEY" \
  "${SERVER_URL:-https://beaverhabits.com}/api/v1/habits/{habit_id}/completions?date_fmt=%25d-%25m-%25Y&date_start={start}&date_end={end}&limit=100&sort=asc"
```

**Step 3** — Render as ASCII table:

```
              Mon   Tue   Wed   Thu   Fri
Clean          ✗     ✗     ✓     ✓     ✓
Call mom       ✗     ✗     ✗     ✗     ✗
Table Tennis   ✗     ✗     ✗     ✗     ✗
Reading        ✗     ✗     ✗     ✗     ✗
```

Use `✓`/`✗` for done/not done. Default to 5 days ending today.

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


## Usage Instructions

- When the user asks to list, show, or check habits, always respond with the ASCII overview table (not a plain list).
- After completing or uncompleting a habit, always re-render the overview table to show the updated state.
- Resolve habit names → IDs via `list_habits`. Never ask the user for a `habit_id`.
- Default to today's date for completions unless specified. Use `date_fmt=%d-%m-%Y`.
