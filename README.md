# Beaver Habit Tracker

![GitHub Release](https://img.shields.io/github/v/release/daya0576/beaverhabits)
![Docker Pulls](https://img.shields.io/docker/pulls/daya0576/beaverhabits)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/daya0576/beaverhabits/fly.yml)
![Uptime Robot ratio (30 days)](https://img.shields.io/uptimerobot/ratio/m787647728-b1a273391c2ad5c526b1c605)

A self-hosted habit tracking app without "Goals"

<img src='https://github.com/daya0576/beaverhabits/assets/6239652/0418fa41-8985-46ef-b623-333b62b2f92e' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/c0ce98cf-5a44-4bbc-8cd3-c7afb20af671' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/516c19ca-9f55-4c21-9e6d-c8f0361a5eb2' width='250'>


# Derivatives

[Beaver Habit Tracker API How‐to Guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide)

- [HabitDeck](https://github.com/nov1n/HabitDeck): Turn your Stream Deck into an interactive habit tracker
- [Apple Shortcut](https://github.com/daya0576/beaverhabits/discussions/50#discussion-7746029): A shortcut for sharing the App on iPhone
- [Home Assistant Switch](https://github.com/daya0576/beaverhabits/issues/55#issuecomment-2569685687): A switch for home assistant to mark a habit as done
- ...


# Getting Started

## Cloud

- Demo: https://beaverhabits.com/demo
- Login: https://beaverhabits.com

## Self-Hosting

### Unraid

Simply search for "Beaver Habit Tracker" in the Community Apps store!

### Ship with Docker

```bash
docker run -d --name beaverhabits \
  -u $(id -u):$(id -g) \
  -e HABITS_STORAGE=USER_DISK \
  -v /path/to/host/directory:/app/.user/ \
  -p 8080:8080 \
  daya0576/beaverhabits:latest
```

Or Docker Compose:
```yaml
services:
  beaverhabits:
    container_name: beaverhabits
    user: 1000:1000 # User permissions of your docker or default user.
    environment:
      # See the note below to find all the environment variables
      - HABITS_STORAGE=USER_DISK # DATABASE stores in a single SQLite database named habits.db. USER_DISK option saves in a local json file.
      - TRUSTED_LOCAL_EMAIL=your@email.com # Skip authentication
      - INDEX_HABIT_DATE_COLUMNS=5 # Customize the date columns for the index page.
      - ENABLE_IOS_STANDALONE=true
    volumes:
      - /path/to/beaver/habits:/app/.user/ # Change directory to match your docker file scheme.
    ports:
      - 8080:8080
    restart: unless-stopped
    image: daya0576/beaverhabits:latest
```

P.S. The container starts as nobody to increase the security and make it OpenShift compatible.
To avoid [permission issues](https://github.com/daya0576/beaverhabits/discussions/31), ensure that the UID owning the host folder aligns with the UID of the user inside the container.

## Options

| Name | Description |
|:--|:--|
| **HABITS_STORAGE**(str) | The `DATABASE` option stores everything in a single SQLite database file named habits.db. On the other hand, the `USER_DISK` option saves habits and records in a local json file. |
| **FIRST_DAY_OF_WEEK**(int) | By default, the first day of the week is set as Monday. To change it to Sunday, you can set it as `6`. |
| **MAX_USER_COUNT**(int) | By setting it to `1`, you can prevent others from signing up in the future. |
| **ENABLE_IOS_STANDALONE**(bool) | Experiential feature to  enable standalone mode on iOS. The default setting is `false`. |
| **INDEX_SHOW_HABIT_COUNT**(bool) | To display total completed count along with the habit name on the index page. The default setting is `false`. |
| **INDEX_HABIT_NAME_COLUMNS**(int) | Customize the habit name column count for the index page. The default value is `5`. |
| **INDEX_HABIT_DATE_COLUMNS**(int) | Customize the date column count for the index page. The default value is `5`. |
| **TRUSTED_EMAIL_HEADER**(str) | Delegate authentication to an authenticating reverse proxy that passes in the user's details in HTTP headers, e.g. `Cf-Access-Authenticated-User-Email`. An existing account is required. |
| **TRUSTED_LOCAL_EMAIL**(str) | Disables authentication entirely. A new account with the specified email will be created if it does not exist. |
| **INDEX_HABIT_DATE_REVERSE**(bool) | Reverse the order of dates to display (default value is false). |
| **UMAMI_ANALYTICS_ID**(str) | Umami analytics tracking id. If left empty (default) no tracking snippet will be injected. |

## Development

BeaverHabits favors [uv](https://docs.astral.sh/uv/getting-started/) as package management tool. Here is how to set up the development environment:

```sh
# Install uv and all the dependencies
uv venv && uv sync

# Start the server
./start.sh dev
```

# Features

Checkout the [wiki](https://github.com/daya0576/beaverhabits/wiki) page for a full list of features, and [vote](https://github.com/daya0576/beaverhabits/discussions/78) for your most wanted features.

- Daily notes/descriptions
- Streaks
- Export & Import
- Reorder habits
- SSO Trusted email header
- ...

Here are my table tennis training sessions over the past year ^^

<img width="750" alt="image" src="https://github.com/user-attachments/assets/1b01435e-5327-4dc6-96d1-1738e2647e53" />

# Sponsor
<a href="https://www.buymeacoffee.com/henryzhu" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy Me A Coffee" height="41" width="174"></a>
