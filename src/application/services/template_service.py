"""テンプレート操作に関するアプリケーションサービス。"""
from __future__ import annotations

from dataclasses import dataclass

from domain import Template, TemplateScope
from domain.interfaces.repositories import TemplateRepository
from domain.services.template_service import merge_templates
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

    def get_template_overview(
        self, *, user_id: int, guild_id: int | None
    ) -> tuple[TemplateListDTO, TemplateListDTO, TemplateListDTO]:
        """ユーザー向けのテンプレート一覧を取得する。"""

        user = self._repository.get_user(
            user_id,
            guild_id=guild_id,
            include_shared=True,
        )

        if user is not None:
            private = TemplateListDTO(
                templates=list(getattr(user, "custom_templates", [])),
                scope=TemplateScope.PRIVATE,
            )
            guild_templates = TemplateListDTO(
                templates=list(getattr(user, "shared_templates", [])),
                scope=TemplateScope.GUILD,
            )
            public = TemplateListDTO(
                templates=list(getattr(user, "public_templates", [])),
                scope=TemplateScope.PUBLIC,
            )
            return private, guild_templates, public

        guild_templates, public_shared = self._repository.get_shared_templates_for_user(
            guild_id=guild_id
        )
        default_templates = self._repository.get_default_templates()
        private = TemplateListDTO(templates=[], scope=TemplateScope.PRIVATE)
        guild = TemplateListDTO(templates=list(guild_templates), scope=TemplateScope.GUILD)
        public = TemplateListDTO(
            templates=list(merge_templates(public_shared, default_templates)),
            scope=TemplateScope.PUBLIC,
        )
        return private, guild, public

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

    def delete_user_template_by_id(self, *, user_id: int, template_id: str) -> None:
        """テンプレート ID を指定してユーザーのテンプレートを削除する。"""

        self._repository.delete_custom_template(
            user_id=user_id,
            template_id=template_id,
        )

    def mark_recent_template(self, *, user_id: int, template: Template) -> None:
        """最近利用したテンプレートとして保存する。"""

        self._repository.set_least_template(user_id, template)

    def update_user_template(self, *, user_id: int, template: Template) -> Template:
        """ユーザーのテンプレートを更新する。"""

        self._repository.update_custom_template(user_id, template)
        return template

    def list_shared_templates_by_scope(
        self,
        *,
        scope: TemplateScope,
        guild_id: int | None = None,
        created_by: int | None = None,
    ) -> TemplateListDTO:
        """共有/公開テンプレートをスコープ単位で取得する。"""

        templates = self._repository.list_shared_templates(
            scope=scope,
            guild_id=guild_id,
            created_by=created_by,
        )
        return TemplateListDTO(templates=list(templates), scope=scope)

    def create_shared_template(self, template: Template) -> Template:
        """共有テンプレートを新規作成する。"""

        return self._repository.create_shared_template(template)

    def delete_shared_template(self, template_id: str) -> None:
        """共有/公開テンプレートを削除する。"""

        self._repository.delete_shared_template(template_id)

    def get_recent_template(
        self, *, user_id: int, guild_id: int | None
    ) -> Template | None:
        """ユーザーが直近使用したテンプレートを取得する。"""

        user = self._repository.get_user(user_id, guild_id=guild_id)
        return getattr(user, "least_template", None) if user else None


__all__ = ["TemplateApplicationService", "TemplateCopyResultDTO"]
