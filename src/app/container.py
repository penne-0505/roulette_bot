from __future__ import annotations

from dataclasses import dataclass

from injector import Injector

from app.config import AppConfig
from presentation.discord.client import BotClient
from presentation.discord.commands.registry import register_commands


@dataclass(slots=True)
class DiscordApplication:
    """Discord Bot のクライアントとトークンを束ねたアプリケーションコンテナ。"""

    client: BotClient
    token: str

    async def run(self) -> None:
        async with self.client:
            await self.client.start(self.token)


def build_discord_application(injector: Injector) -> DiscordApplication:
    """DI コンテナを利用して Discord アプリケーションを組み立てる。"""

    config = injector.get(AppConfig)
    client = injector.get(BotClient)
    register_commands(client)
    return DiscordApplication(client=client, token=config.discord.token)


__all__ = ["DiscordApplication", "build_discord_application"]
