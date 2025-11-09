"""Discord クライアント周りの互換エントリポイント。"""
from presentation.discord.client import BotClient
from presentation.discord.commands.registry import register_commands
from .config import load_client_token

__all__ = [
    "BotClient",
    "register_commands",
    "load_client_token",
]
