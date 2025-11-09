"""あみだくじフローのオーケストレーションを担うサービス。"""
from __future__ import annotations

from dataclasses import dataclass

import discord

from application.dto import (
    FlowTransitionDTO,
    HistoryUsageResultDTO,
    TemplateCreationResultDTO,
    TemplateDeletionResultDTO,
)
from application.services.template_service import TemplateApplicationService
from domain import Template
from models.state_model import AmidakujiState


@dataclass(slots=True)
class FlowContext:
    """フロー遷移の判定に利用する最小限の情報。"""

    is_main_flow: bool


class AmidakujiFlowService:
    """フロー状態遷移をアプリケーション層で統制するサービス。"""

    def __init__(self, template_service: TemplateApplicationService) -> None:
        self._template_service = template_service

    def complete_template_creation(
        self,
        *,
        user_id: int,
        template: Template,
        context: FlowContext,
        interaction: discord.Interaction | None,
    ) -> TemplateCreationResultDTO:
        """テンプレート作成完了時の処理を行う。"""

        self._template_service.create_user_template(user_id=user_id, template=template)

        transition: FlowTransitionDTO | None = None
        if context.is_main_flow:
            transition = FlowTransitionDTO(
                next_state=AmidakujiState.TEMPLATE_DETERMINED,
                result=template,
                interaction=interaction,
            )

        return TemplateCreationResultDTO(template=template, transition=transition)

    def remove_template(
        self,
        *,
        user_id: int,
        template_title: str,
        interaction: discord.Interaction | None,
    ) -> TemplateDeletionResultDTO:
        """テンプレート削除時の処理を行う。"""

        self._template_service.delete_user_template(
            user_id=user_id, template_title=template_title
        )
        transition = FlowTransitionDTO(
            next_state=AmidakujiState.MODE_USE_EXISTING,
            result=interaction,
            interaction=interaction,
        )
        return TemplateDeletionResultDTO(title=template_title, transition=transition)

    def use_recent_template(
        self,
        *,
        user_id: int,
        guild_id: int | None,
        interaction: discord.Interaction | None,
    ) -> HistoryUsageResultDTO:
        """履歴テンプレート利用時の処理を行う。"""

        template = self._template_service.get_recent_template(
            user_id=user_id, guild_id=guild_id
        )
        if template is None:
            raise LookupError("履歴テンプレートが見つかりません。")

        transition = FlowTransitionDTO(
            next_state=AmidakujiState.TEMPLATE_DETERMINED,
            result=template,
            interaction=interaction,
        )
        return HistoryUsageResultDTO(template=template, transition=transition)


__all__ = ["AmidakujiFlowService", "FlowContext"]
