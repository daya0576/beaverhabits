# Beaver Habit Tracker

![GitHub Release](https://img.shields.io/github/v/release/daya0576/beaverhabits)
![Docker Image Size](https://img.shields.io/docker/image-size/daya0576/beaverhabits)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/daya0576/beaverhabits/fly.yml)
![Uptime Robot ratio (30 days)](https://img.shields.io/uptimerobot/ratio/m787647728-b1a273391c2ad5c526b1c605)

A self hosted habit tracker app to track your fleeting life.

<img src='https://github.com/daya0576/beaverhabits/assets/6239652/0418fa41-8985-46ef-b623-333b62b2f92e' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/c0ce98cf-5a44-4bbc-8cd3-c7afb20af671' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/516c19ca-9f55-4c21-9e6d-c8f0361a5eb2' width='250'>

# Getting Started

## Cloud Service

- Demo: https://beaverhabits.com/demo
- Login: https://beaverhabits.com

## Self-hosting

### Ship with Docker

Example:

```bash
docker run -d --name beaverhabits \
  -e FIRST_DAY_OF_WEEK=0 \
  -e HABITS_STORAGE=USER_DISK \
  -p 8080:8080 \
  --restart unless-stopped \
  daya0576/beaverhabits:latest
```

Options:

- **HABITS_STORAGE**(str): `DATABASE`(default), `USER_DISK`
- **DATABASE_URL**(str): The database url for storage backend, e.g. `sqlite:///habits.db`
- **FIRST_DAY_OF_WEEK**(int): `0`(default), `6`

# Features

1. Pages
   - [x] Index page
   - [x] Habit list page
   - [x] Habit detail page
     - [x] Last three months
     - [x] Calendar heatmap over years
2. Storage:
   - [x] Session-based disk storage
   - [x] User-based disk storage
   - [x] User-based sqlite storage
3. CICD:
   - [x] Custom domain
   - [x] Self-hosting option
   - [x] Unit tests & deployment pipeline
4. Others:
   - [x] Export
   - [ ] Import
   - [x] User management
   - [x] User timezone

# Future Plans

1. Native mobile app
2. Habit calendar template, e.g. vacations
