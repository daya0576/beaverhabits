# Beaver Habit Tracker

![GitHub Release](https://img.shields.io/github/v/release/daya0576/beaverhabits)
![Docker Pulls](https://img.shields.io/docker/pulls/daya0576/beaverhabits)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/daya0576/beaverhabits/fly.yml)
![Uptime Robot ratio (30 days)](https://img.shields.io/uptimerobot/ratio/m796940918-864324d021343c6ace874b58)

A self-hosted habit tracking app without "Goals"

<img src='https://github.com/daya0576/beaverhabits/assets/6239652/0418fa41-8985-46ef-b623-333b62b2f92e' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/c0ce98cf-5a44-4bbc-8cd3-c7afb20af671' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/516c19ca-9f55-4c21-9e6d-c8f0361a5eb2' width='250'>

# Derivatives

[Beaver Habit Tracker API How‐to Guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide)

- [HabitDeck](https://github.com/nov1n/HabitDeck): Turn your Stream Deck into an interactive habit tracker
- [Apple Shortcut](https://github.com/daya0576/beaverhabits/discussions/50#discussion-7746029): A shortcut for sharing the App on iPhone
- [Home Assistant Switch](https://github.com/daya0576/beaverhabits/issues/55#issuecomment-2569685687): A switch for home assistant to mark a habit as done
- [CalDAV bridge](https://github.com/daya0576/beaverhabits/discussions/114): Run a calDAV server that hosts the habits as tasks
- ...


# Getting Started

## Cloud Service (SaaS)

Zero configuration, high availability, and low latency powered by global edge network.

- Demo: https://beaverhabits.com/demo
- Pricing Plans: https://beaverhabits.com

## Self-Hosting

### Unraid

Simply search for "Beaver Habit Tracker" in the Community Apps store!

### Ship with Docker

```bash
docker run -d --name beaverhabits \
  -u $(id -u):$(id -g) \
  -e HABITS_STORAGE=USER_DISK \
  -v ./beaver/:/app/.user/ \
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
      # See the link below to find all the environment variables
      # https://github.com/daya0576/beaverhabits/wiki/Development#options
      - HABITS_STORAGE=USER_DISK # DATABASE stores in a single SQLite database named habits.db. USER_DISK option saves in a local json file.
      - TRUSTED_LOCAL_EMAIL=your@email.com # Skip authentication
      - INDEX_HABIT_DATE_COLUMNS=5 # Customize the date columns for the index page.
      - ENABLE_IOS_STANDALONE=true
    volumes:
      - ./beaver/:/app/.user/ # Change directory to match your docker file scheme.
    ports:
      - 8080:8080
    restart: unless-stopped
    image: daya0576/beaverhabits:latest
```

P.S. The container starts as nobody to increase the security and make it OpenShift compatible.
To avoid [permission issues](https://github.com/daya0576/beaverhabits/discussions/31), ensure that the UID owning the host folder aligns with the UID of the user inside the container.


## Development

BeaverHabits favors [uv](https://docs.astral.sh/uv/getting-started/) as package management tool. Here is how to set up the development environment:

```sh
# Install uv and all the dependencies
uv venv && uv sync

# Start the server
./start.sh dev
```

# Features

For a complete list of features, please visit our [Wiki page](https://github.com/daya0576/beaverhabits/wiki).

Inspired by:
- Android mobile app "Loop Habit Tracker" created by [@iSoron](https://github.com/iSoron/uhabits)
- NiceGUI Todo List example from [@zauberzeug](https://github.com/zauberzeug)

# Sponsor
<a href="https://www.buymeacoffee.com/henryzhu" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy Me A Coffee" height="41" width="174"></a>
