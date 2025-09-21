# Roulette DS Bot

> Status: v0.1.0 (initial release)

Roulette DS Bot is a Discord bot that helps teams run fair amidakuji-style assignments. It offers guided flows for creating, sharing, copying, and deleting templates as well as rich result embeds that summarize assignments.

## Features
- Slash commands for latency checks and amidakuji template workflows
- Interactive Discord UI components for managing options and template lifecycles
- Firebase-backed persistence for user templates, shared templates, and history entries
- Result embed generation with compact and detailed layouts plus selection mode toggles
- Comprehensive unit tests covering flow handlers, data processing, and persistence layers

## Requirements
- Python 3.12+
- Poetry 1.8+
- Discord Bot Token (`CLIENT_TOKEN`)
- Firebase credential reference (`FIREBASE_CREDENTIALS`)

## Quick Start (local)
1. Copy `.env.example` to `.env` and fill in the required values.
2. Install dependencies: `poetry install`.
3. Run the bot: `poetry run python src/main.py`.

### Running the test suite
- Execute all tests with `poetry run pytest`.

## Docker Deployment
1. Build the image: `docker build -t roulette-bot .`.
2. Run the container:
   ```bash
   docker run -e CLIENT_TOKEN=<your_token> \
              -e FIREBASE_CREDENTIALS=<your_credentials_url> \
              -p 8000:8000 \
              roulette-bot
   ```
3. Alternatively, use docker-compose: `docker-compose up --build`.

## Documentation Map
- `docs/guides/`: How-to guides and operational tips.
- `docs/plans/`: Roadmaps and improvement plans.
- `docs/references/`: Reference materials and data schemas.
- `docs/standards/`: Coding conventions and review checklists.
- `CHANGELOG.md`: Release history and notable changes.

## Additional Notes
- Logging configuration lives under `src/app/logging.py` and defaults to structured JSON output.
- Firebase credentials can point to a local path or remote URL; the loader will download and cache as needed.
