from __future__ import annotations

import asyncio
import logging

from app import build_discord_application, configure_logging, load_config
from utils import ERROR, INFO


async def run_bot() -> None:
    try:
        config = load_config()
    except RuntimeError as exc:
        logging.error(ERROR + str(exc))
        return

    application = build_discord_application(config)

    logging.info(INFO + "Client initialized. Setup hook will handle command sync.")
    await application.run()


def main() -> None:
    configure_logging()
    logging.info(INFO + "Starting Discord client event loop.")
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
