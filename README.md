# Beaver Prime Habit Tracker


A self-hosted habit tracking app without "Goals"

<img src='https://github.com/daya0576/beaverhabits/assets/6239652/0418fa41-8985-46ef-b623-333b62b2f92e' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/c0ce98cf-5a44-4bbc-8cd3-c7afb20af671' width='250'>
<img src='https://github.com/daya0576/beaverhabits/assets/6239652/516c19ca-9f55-4c21-9e6d-c8f0361a5eb2' width='250'>

# What's New in This Fork

## Enhanced Features

This fork adds several powerful enhancements:

1. **List Support**: Organize habits into custom lists for better organization
2. **Weekly Goals**: Set target number of completions per week for each habit
3. **Quick Filtering**: Filter habits by first letter for faster access
4. **Enhanced API Support**: Powerful API endpoints for managing habits and lists. See [API Documentation](API.md) for detailed information about available endpoints and usage examples.

# Derivatives

- [HabitDeck](https://github.com/nov1n/HabitDeck): Turn your Stream Deck into an interactive habit tracker
- [Apple Shortcut](https://github.com/daya0576/beaverhabits/discussions/50#discussion-7746029): A shortcut for sharing the App on iPhone
- [Home Assistant Switch](https://github.com/daya0576/beaverhabits/issues/55#issuecomment-2569685687): A switch for home assistant to mark a habit as done
- ...

# Getting Started

## Self-Hosting


## Development

BeaverPrime favors [uv](https://docs.astral.sh/uv/getting-started/) as package management tool. Here is how to set up the development environment:

```sh
# Install uv and all the dependencies
uv venv && uv sync

# Start the server
./start.sh dev
```

## Import

To import from an existing setup, e.g. uhabit, please check this [wiki](https://github.com/daya0576/beaverhabits/wiki/Import-from-Existing-Setup) for more details.

## Standalone mode for iOS (Web Application)

Please follow this [wiki](<https://github.com/daya0576/beaverhabits/wiki/To-Add-Standalone-Mode-for-iOS-(Web-Application)>) to add it as an icon on the home screen and make it launch in a separate window

## Reorder Habits

Open page `/gui/order` to change the order of habits.

## REST APIs

[Beaver Habit Tracker API How‐to Guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide)

## Daily Notes

Press and hold to add a note or description for the day.
