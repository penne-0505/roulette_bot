"""テンプレート操作に関するアプリケーションサービス。"""
from __future__ import annotations

from dataclasses import dataclass

from domain import Template, TemplateScope
from domain.interfaces.repositories import TemplateRepository
from application.dto import TemplateListDTO


@dataclass(slots=True)
class TemplateCopyResultDTO:
    """共有テンプレートコピーの結果 DTO."""

    template: Template


class TemplateApplicationService:
    """テンプレート操作のユースケースサービス。"""

    def __init__(self, repository: TemplateRepository) -> None:
        self._repository = repository

    def list_private_templates(
        self, *, user_id: int, guild_id: int | None
    ) -> TemplateListDTO:
        """ユーザーのプライベートテンプレート一覧を取得する。"""

        user = self._repository.get_user(user_id, guild_id=guild_id)
        templates = [
            template
            for template in getattr(user, "custom_templates", [])
            if template.scope is TemplateScope.PRIVATE
        ] if user else []
        return TemplateListDTO(templates=list(templates), scope=TemplateScope.PRIVATE)

    def list_shared_templates(self, *, guild_id: int) -> TemplateListDTO:
        """サーバー共有テンプレートを取得する。"""

        shared_templates, _ = self._repository.get_shared_templates_for_user(
            guild_id=guild_id
        )
        return TemplateListDTO(templates=list(shared_templates), scope=TemplateScope.GUILD)

    def list_public_templates(self) -> TemplateListDTO:
        """公開テンプレートを取得する。"""

        _, public_templates = self._repository.get_shared_templates_for_user(guild_id=None)
        return TemplateListDTO(templates=list(public_templates), scope=TemplateScope.PUBLIC)

    def copy_shared_template(
        self, *, user_id: int, template: Template
    ) -> TemplateCopyResultDTO:
        """共有/公開テンプレートをユーザーにコピーする。"""

        copied = self._repository.copy_shared_template_to_user(user_id, template)
        return TemplateCopyResultDTO(template=copied)

    def create_user_template(self, *, user_id: int, template: Template) -> Template:
        """ユーザーのテンプレートを作成する。"""

        self._repository.add_custom_template(user_id=user_id, template=template)
        return template

    def delete_user_template(self, *, user_id: int, template_title: str) -> None:
        """ユーザーのテンプレートを削除する。"""

        self._repository.delete_custom_template(
            user_id=user_id,
            template_title=template_title,
        )

    def mark_recent_template(self, *, user_id: int, template: Template) -> None:
        """最近利用したテンプレートとして保存する。"""

        self._repository.set_least_template(user_id, template)

    def get_recent_template(
        self, *, user_id: int, guild_id: int | None
    ) -> Template | None:
        """ユーザーが直近使用したテンプレートを取得する。"""

        user = self._repository.get_user(user_id, guild_id=guild_id)
        return getattr(user, "least_template", None) if user else None


__all__ = ["TemplateApplicationService", "TemplateCopyResultDTO"]
