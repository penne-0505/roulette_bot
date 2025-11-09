"""ドメイン層で利用するリポジトリインタフェース。"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .. import (
    AssignmentHistory,
    PairList,
    ResultEmbedMode,
    SelectionMode,
    Template,
    TemplateScope,
    UserInfo,
)


class TemplateRepository(Protocol):
    """テンプレートおよびユーザーデータを扱うリポジトリ。"""

    def ensure_required_collections(self) -> None:
        ...

    def ensure_default_templates(self) -> list[Template]:
        ...

    def get_default_templates(self) -> list[Template]:
        ...

    def list_shared_templates(
        self,
        *,
        scope: TemplateScope | None = None,
        guild_id: int | None = None,
        created_by: int | None = None,
    ) -> list[Template]:
        ...

    def get_shared_templates_for_user(
        self, *, guild_id: int | None
    ) -> tuple[list[Template], list[Template]]:
        ...

    def toggle_embed_mode(self) -> None:
        ...

    def get_embed_mode(self) -> str:
        ...

    def set_embed_mode(self, mode: ResultEmbedMode | str) -> None:
        ...

    def set_selection_mode(self, mode: SelectionMode | str) -> None:
        ...

    def get_selection_mode(self) -> str:
        ...

    def save_history(
        self,
        *,
        guild_id: int,
        template: Template,
        pairs: PairList,
        selection_mode: SelectionMode | str,
    ) -> None:
        ...

    def get_recent_history(
        self,
        *,
        guild_id: int,
        template_title: str | None = None,
        limit: int = 10,
        since: datetime | None = None,
    ) -> list[AssignmentHistory]:
        ...

    def init_user(self, user_id: int, name: str) -> None:
        ...

    def set_user(self, user: UserInfo) -> None:
        ...

    def get_user(
        self,
        user_id: int,
        *,
        guild_id: int | None = None,
        include_shared: bool = True,
    ) -> UserInfo | None:
        ...

    def delete_user(self, user_id: int) -> None:
        ...

    def user_is_exist(self, user_id: int) -> bool:
        ...

    def add_custom_template(self, user_id: int, template: Template) -> None:
        ...

    def update_custom_template(self, user_id: int, template: Template) -> None:
        ...

    def delete_custom_template(
        self,
        user_id: int,
        *,
        template_id: str | None = None,
        template_title: str | None = None,
    ) -> None:
        ...

    def set_least_template(self, user_id: int, template: Template) -> None:
        ...

    def create_shared_template(self, template: Template) -> Template:
        ...

    def delete_shared_template(self, template_id: str) -> None:
        ...

    def copy_shared_template_to_user(self, user_id: int, template: Template) -> Template:
        ...


__all__ = ["TemplateRepository"]
