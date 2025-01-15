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

- [HabitDeck](https://github.com/nov1n/HabitDeck): Turn your Steam Deck into an interactive habit tracker
- [Apple Shortcut](https://github.com/daya0576/beaverhabits/discussions/50#discussion-7746029): A shortcut for sharing the App on iPhone
- [Home Assistant Switch](https://github.com/daya0576/beaverhabits/issues/55#issuecomment-2569685687): A switch for home assistant to mark a habit as done
- ...

# Getting Started

## Cloud Service

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
| **ENABLE_IOS_STANDALONE**(bool) | Experiential feature to  enable standalone mode on iOS. The default setting is `false` |
| **INDEX_SHOW_HABIT_COUNT**(bool) | To display the total completed count badge on the main page. The default setting is `false` |

## Development

BeaverHabits favors [uv](https://docs.astral.sh/uv/getting-started/) as package management tool. Here is how to set up the development environment:

```sh
# Install uv and all the dependencies
uv venv && uv sync

# Start the server
./start.sh dev
```

# Features

1. Pages
   - [x] Index page
   - [x] Habit list page
     - [x] Order habits
   - [x] Habit detail page
     - [x] Calendar
     - [x] Streaks
2. Storage:
   - [x] Session-based disk storage
   - [x] User-based disk storage
   - [x] User-based db storage
3. CICD:
   - [x] Custom domain
   - [x] Self-hosting option
   - [x] Unit tests & deployment pipeline
4. Others:
   - [x] Export
   - [x] Import
   - [x] User management
   - [x] User timezone
   - [x] RESTful API

## Streaks
Here are my table tennis training sessions in the past year :)

<img width="800" alt="image" src="https://github.com/user-attachments/assets/db795af7-ed32-4879-b629-9fd3a2700440" />

## Import
To import from an existing setup, e.g. uhabit, please check this [wiki](https://github.com/daya0576/beaverhabits/wiki/Import-from-Existing-Setup) for more details.

## Standalone mode for iOS (Web Application)
Please follow this [wiki](https://github.com/daya0576/beaverhabits/wiki/To-Add-Standalone-Mode-for-iOS-(Web-Application)) to add it as an icon on the home screen and make it launch in a separate window

## Reorder Habits
Open page `/gui/order` to change the order of habits.

## REST APIs
[Beaver Habit Tracker API How‐to Guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide)

# Future Plans

1. Quantitative metrics
2. Native mobile app -- can't wait to try Swift or Tauri :p
3. Habit calendar template, e.g. vacations
4. Category or Folders
5. ...
