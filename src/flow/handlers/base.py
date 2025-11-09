"""フローハンドラで共通利用される基底クラスとヘルパー群。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

import discord

from application.services.flow_service import AmidakujiFlowService
from application.services.history_service import HistoryApplicationService
from application.services.template_service import TemplateApplicationService
from flow.actions import FlowAction, SendMessageAction
from models.context_model import CommandContext


class BaseStateHandler(ABC):
    """状態ハンドラ共通の抽象クラス。"""

    @abstractmethod
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction] | None:
        """現在のステートに応じたアクションを返す。"""


def _resolve_service(
    services: Any,
    candidate_names: tuple[str, ...],
    expected_type: type,
) -> Any:
    for name in candidate_names:
        candidate = getattr(services, name, None)
        if candidate is not None:
            return candidate
    raise RuntimeError(f"{expected_type.__name__} が利用できません。")


def resolve_template_service(services: Any) -> TemplateApplicationService:
    """テンプレートユースケースサービスを解決する。"""

    return _resolve_service(
        services,
        ("template_service",),
        TemplateApplicationService,
    )


def resolve_history_service(services: Any) -> HistoryApplicationService:
    """履歴ユースケースサービスを解決する。"""

    return _resolve_service(
        services,
        ("history_service",),
        HistoryApplicationService,
    )


def resolve_flow_service(services: Any) -> AmidakujiFlowService:
    """フローオーケストレーションサービスを解決する。"""

    return _resolve_service(
        services,
        ("amidakuji_flow_service",),
        AmidakujiFlowService,
    )


def build_ephemeral_embed_action(
    *,
    title: str,
    description: str,
    color: discord.Color,
) -> SendMessageAction:
    """エフェメラルな埋め込みを送信するアクションを組み立てる。"""

    embed = discord.Embed(title=title, description=description, color=color)
    return SendMessageAction(embed=embed, ephemeral=True)


__all__ = [
    "BaseStateHandler",
    "build_ephemeral_embed_action",
    "resolve_flow_service",
    "resolve_history_service",
    "resolve_template_service",
]
