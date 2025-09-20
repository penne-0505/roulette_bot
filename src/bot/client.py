"""Discordクライアント本体を定義するモジュール。"""
from __future__ import annotations

import logging
import time
from typing import Any

import discord

from services.app_context import create_db_manager
from services.startup_check import StartupSelfCheck
from utils import (
    DATEFORMAT,
    ERROR,
    FORMAT,
    INFO,
    CommandsTranslator,
    blue,
    bold,
    green,
    magenta,
    yellow,
)


class BotClient(discord.Client):
    """Discordボット用のクライアント。"""

    def __init__(
        self,
        *,
        intents: discord.Intents | None = None,
        translator: discord.app_commands.Translator | None = None,
    ) -> None:
        super().__init__(intents=intents or discord.Intents.all())
        self.start_time = time.time()
        self.db = create_db_manager()
        self.tree = discord.app_commands.CommandTree(self)
        self._translator = translator or CommandsTranslator()

    async def setup_hook(self) -> None:
        await self.tree.set_translator(self._translator)
        await self.tree.sync()
        logging.info(INFO + "Application commands synchronized.")

    async def on_ready(self) -> None:
        self.db.ensure_default_templates()

        checker = StartupSelfCheck(self.db)
        if not checker.run(discord_client=self):
            logging.error(ERROR + "Critical startup check failed. Shutting down client.")
            await self.close()
            return

        logging.info(
            INFO + f"Logged in as {green(self.user.name)} ({blue(self.user.id)})"
        )
        logging.info(INFO + f"Connected to {green(str(len(self.guilds)))} guilds")
        logging.info(INFO + f"Launch time: {green(str(time.time() - self.start_time))}s")
        logging.info(INFO + bold("Bot is ready."))

    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ) -> None:
        exec_user = interaction.user
        user_id = exec_user.id
        if not self.db.user_is_exist(user_id):
            self.db.init_user(user_id=user_id, name=exec_user.name)

        exec_guild = yellow(interaction.guild) if interaction.guild else "DM"
        exec_channel = magenta(interaction.channel) if interaction.channel else "(DM)"
        user_name = blue(exec_user.name)
        user_id_colored = blue(exec_user.id)
        exec_command = green(command.name)
        logging.info(
            INFO
            + f"Command executed by {user_name}({user_id_colored}): {exec_command} in {exec_guild}({exec_channel})"
        )


__all__ = ["BotClient"]
