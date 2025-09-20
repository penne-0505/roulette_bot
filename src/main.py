from __future__ import annotations

import asyncio
import logging

from bot import BotClient, load_client_token, register_commands
from utils import DATEFORMAT, ERROR, FORMAT, INFO


logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt=DATEFORMAT)


async def run_bot() -> None:
    try:
        token = load_client_token()
    except RuntimeError as exc:
        logging.error(ERROR + str(exc))
        return

    client = BotClient()
    register_commands(client)

    logging.info(INFO + "Client initialized. Setup hook will handle command sync.")

    async with client:
        logging.info(INFO + "Starting Discord client event loop.")
        await client.start(token)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
