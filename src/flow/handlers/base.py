"""フローハンドラで共通利用される基底クラスとヘルパー群。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, NamedTuple

import discord

from flow.actions import FlowAction, SendMessageAction
from models.context_model import CommandContext
from models.model import TemplateScope, UserInfo
from models.state_model import AmidakujiState

if TYPE_CHECKING:  # pragma: no cover
    from db_manager import DBManager


class BaseStateHandler(ABC):
    """状態ハンドラ共通の抽象クラス。"""

    @abstractmethod
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction] | None:
        """現在のステートに応じたアクションを返す。"""


def get_db_manager_from_source(source: Any) -> Any:
    """安全に DBManager を取得するためのヘルパー。"""

    return getattr(source, "db", None) if source is not None else None


def resolve_db_manager(context: CommandContext, services: Any) -> "DBManager":
    db_manager = get_db_manager_from_source(services)
    if db_manager is None:
        interaction_client = getattr(context.interaction, "client", None)
        db_manager = get_db_manager_from_source(interaction_client)
    if db_manager is None:
        raise RuntimeError("DB manager is not available")
    return db_manager


class UserContext(NamedTuple):
    """ユーザー/ギルド情報をまとめたコンテナ。"""

    db_manager: "DBManager"
    user_data: UserInfo | None
    guild_id: int | None


def resolve_user_context(
    context: CommandContext,
    services: Any,
) -> UserContext:
    db_manager = resolve_db_manager(context, services)
    interaction = context.interaction
    guild_id = getattr(interaction, "guild_id", None)
    user_id = getattr(interaction.user, "id", None)
    user_data = db_manager.get_user(user_id, guild_id=guild_id) if user_id else None
    return UserContext(db_manager=db_manager, user_data=user_data, guild_id=guild_id)


def build_ephemeral_embed_action(
    *,
    title: str,
    description: str,
    color: discord.Color,
) -> SendMessageAction:
    """エフェメラルな埋め込みを送信するアクションを組み立てる。"""

    embed = discord.Embed(title=title, description=description, color=color)
    return SendMessageAction(embed=embed, ephemeral=True)


def filter_private_templates(user_info: UserInfo | None) -> list:
    """ユーザー所有テンプレートのうち PRIVATE のものだけを返す。"""

    if user_info is None:
        return []
    return [
        template
        for template in getattr(user_info, "custom_templates", [])
        if template.scope is TemplateScope.PRIVATE
    ]


__all__ = [
    "BaseStateHandler",
    "UserContext",
    "build_ephemeral_embed_action",
    "filter_private_templates",
    "get_db_manager_from_source",
    "resolve_db_manager",
    "resolve_user_context",
]
