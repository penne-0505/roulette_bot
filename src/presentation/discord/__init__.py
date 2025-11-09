"""Discord プレゼンテーション層パッケージ。"""

from .client import BotClient

__all__ = ["BotClient", "register_commands"]


def register_commands(client: BotClient) -> None:
    """遅延インポートでスラッシュコマンドを登録する。"""

    from presentation.discord.commands.registry import register_commands as _register

    _register(client)
