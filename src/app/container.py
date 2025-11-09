from __future__ import annotations

from dataclasses import dataclass

from app.config import AppConfig
from presentation.discord.client import BotClient
from presentation.discord.commands.registry import register_commands
from services.app_context import create_db_manager


@dataclass(slots=True)
class DiscordApplication:
    """Discord Bot のクライアントとトークンを束ねたアプリケーションコンテナ。"""

    client: BotClient
    token: str

    async def run(self) -> None:
        async with self.client:
            await self.client.start(self.token)


def build_discord_application(config: AppConfig) -> DiscordApplication:
    """設定値を基に Discord アプリケーションを組み立てる。"""

    db_manager = create_db_manager(config.firebase.credentials_reference)
    client = BotClient(db_manager=db_manager)
    register_commands(client)
    return DiscordApplication(client=client, token=config.discord.token)


__all__ = ["DiscordApplication", "build_discord_application"]
