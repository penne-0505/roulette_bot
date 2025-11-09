"""Discord ビューが扱う状態オブジェクト。"""
from __future__ import annotations

from dataclasses import dataclass
from application.dto import SharedTemplateSetDTO, TemplateListDTO
from domain import ResultEmbedMode, SelectionMode, Template


@dataclass(slots=True)
class EmbedModeState:
    current_mode: ResultEmbedMode
    user_id: int


@dataclass(slots=True)
class SelectionModeState:
    current_mode: SelectionMode
    user_id: int


@dataclass(slots=True)
class TemplateListViewState:
    """テンプレート一覧表示用の状態。"""

    private_templates: list[Template]
    guild_templates: list[Template]
    public_templates: list[Template]

    @classmethod
    def from_dtos(
        cls, *, private: TemplateListDTO, guild: TemplateListDTO, public: TemplateListDTO
    ) -> "TemplateListViewState":
        return cls(
            private_templates=list(private.templates),
            guild_templates=list(guild.templates),
            public_templates=list(public.templates),
        )


@dataclass(slots=True)
class TemplateManagementState:
    user_id: int
    templates: list[Template]


@dataclass(slots=True)
class TemplateSharingState:
    user_id: int
    display_name: str
    guild_id: int | None
    private_templates: list[Template]
    guild_templates: list[Template]
    public_templates: list[Template]

    @classmethod
    def from_dtos(
        cls,
        *,
        user_id: int,
        display_name: str,
        guild_id: int | None,
        private: TemplateListDTO,
        shared: SharedTemplateSetDTO,
    ) -> "TemplateSharingState":
        return cls(
            user_id=user_id,
            display_name=display_name,
            guild_id=guild_id,
            private_templates=list(private.templates),
            guild_templates=list(shared.shared_templates),
            public_templates=list(shared.public_templates),
        )


__all__ = [
    "EmbedModeState",
    "SelectionModeState",
    "TemplateListViewState",
    "TemplateManagementState",
    "TemplateSharingState",
]
