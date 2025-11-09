from __future__ import annotations

import asyncio
import logging

from app import build_discord_application
from bootstrap import bootstrap_application
from utils import ERROR, INFO


async def run_bot() -> None:
    try:
        context = bootstrap_application()
    except RuntimeError as exc:
        logging.error(ERROR + str(exc))
        return

    logging.info(INFO + "Starting Discord client event loop.")

    application = build_discord_application(context.injector)

    logging.info(INFO + "Client initialized. Setup hook will handle command sync.")
    await application.run()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
