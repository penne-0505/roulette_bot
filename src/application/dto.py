"""アプリケーション層で利用する共通 DTO 群。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import discord

from domain import AssignmentHistory, Template, TemplateScope
from models.state_model import AmidakujiState


@dataclass(frozen=True, slots=True)
class TemplateListDTO:
    """テンプレート一覧のプレゼンテーション向け DTO."""

    templates: list[Template]
    scope: TemplateScope | None = None


@dataclass(frozen=True, slots=True)
class SharedTemplateSetDTO:
    """共有/公開テンプレートをまとめた DTO."""

    shared_templates: list[Template]
    public_templates: list[Template]


@dataclass(frozen=True, slots=True)
class FlowTransitionDTO:
    """フロー状態遷移を表現する DTO."""

    next_state: AmidakujiState
    result: object
    interaction: discord.Interaction | None = None


@dataclass(frozen=True, slots=True)
class TemplateCreationResultDTO:
    """テンプレート作成処理の結果 DTO."""

    template: Template
    transition: FlowTransitionDTO | None


@dataclass(frozen=True, slots=True)
class TemplateDeletionResultDTO:
    """テンプレート削除処理の結果 DTO."""

    title: str
    transition: FlowTransitionDTO


@dataclass(frozen=True, slots=True)
class HistoryUsageResultDTO:
    """履歴テンプレート利用時の結果 DTO."""

    template: Template
    transition: FlowTransitionDTO


@dataclass(frozen=True, slots=True)
class HistorySummaryDTO:
    """履歴情報と関連データをまとめた DTO."""

    histories: list[AssignmentHistory]
    selection_mode: str
    embed_mode: str
    members: Sequence[discord.User]
    template: Template


__all__ = [
    "FlowTransitionDTO",
    "HistorySummaryDTO",
    "HistoryUsageResultDTO",
    "SharedTemplateSetDTO",
    "TemplateCreationResultDTO",
    "TemplateDeletionResultDTO",
    "TemplateListDTO",
]
