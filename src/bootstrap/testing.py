from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from app.config import AppConfig, DiscordSettings, FirebaseSettings
from app.container import build_discord_application, DiscordApplication
from domain import ResultEmbedMode, SelectionMode, Template
from domain.interfaces.repositories import TemplateRepository

from .app import BootstrapContext, bootstrap_application


class InMemoryTemplateRepository(TemplateRepository):
    """テスト用の簡易 TemplateRepository 実装。"""

    def __init__(self) -> None:
        self.embed_mode: str = ResultEmbedMode.COMPACT.value
        self.selection_mode: str = SelectionMode.RANDOM.value
        self.users: dict[int, object] = {}
        self.saved_histories: list[object] = []

    def ensure_required_collections(self) -> None:
        return None

    def ensure_default_templates(self) -> list[Template]:
        return []

    def get_default_templates(self) -> list[Template]:
        return []

    def list_shared_templates(
        self,
        *,
        scope: object | None = None,
        guild_id: int | None = None,
        created_by: int | None = None,
    ) -> list[Template]:
        return []

    def get_shared_templates_for_user(
        self,
        *,
        guild_id: int | None,
    ) -> tuple[list[Template], list[Template]]:
        return [], []

    def toggle_embed_mode(self) -> None:
        self.embed_mode = (
            ResultEmbedMode.DETAILED.value
            if self.embed_mode == ResultEmbedMode.COMPACT.value
            else ResultEmbedMode.COMPACT.value
        )

    def get_embed_mode(self) -> str:
        return self.embed_mode

    def set_embed_mode(self, mode: ResultEmbedMode | str) -> None:
        self.embed_mode = mode.value if isinstance(mode, ResultEmbedMode) else str(mode)

    def set_selection_mode(self, mode: SelectionMode | str) -> None:
        self.selection_mode = mode.value if isinstance(mode, SelectionMode) else str(mode)

    def get_selection_mode(self) -> str:
        return self.selection_mode

    def save_history(
        self,
        *,
        guild_id: int,
        template: Template,
        pairs: object,
        selection_mode: SelectionMode | str,
    ) -> None:
        self.saved_histories.append((guild_id, template, pairs, selection_mode))

    def get_recent_history(
        self,
        *,
        guild_id: int,
        template_title: str | None = None,
        limit: int = 10,
        since: object | None = None,
    ) -> list[object]:
        return []

    def init_user(self, user_id: int, name: str) -> None:
        self.users[user_id] = {"name": name}

    def set_user(self, user: object) -> None:
        if isinstance(user, dict) and "user_id" in user:
            self.users[user["user_id"]] = user

    def get_user(
        self,
        user_id: int,
        *,
        guild_id: int | None = None,
        include_shared: bool = True,
    ) -> object | None:
        return self.users.get(user_id)

    def delete_user(self, user_id: int) -> None:
        self.users.pop(user_id, None)

    def user_is_exist(self, user_id: int) -> bool:
        return user_id in self.users

    def add_custom_template(self, user_id: int, template: Template) -> None:
        self.users.setdefault(user_id, {"custom_templates": []}).setdefault(
            "custom_templates", []
        ).append(template)

    def update_custom_template(self, user_id: int, template: Template) -> None:
        templates = self.users.setdefault(user_id, {}).setdefault("custom_templates", [])
        for index, current in enumerate(templates):
            if getattr(current, "id", None) == getattr(template, "id", None):
                templates[index] = template
                return
        templates.append(template)

    def delete_custom_template(
        self,
        user_id: int,
        *,
        template_id: str | None = None,
        template_title: str | None = None,
    ) -> None:
        templates = self.users.setdefault(user_id, {}).setdefault("custom_templates", [])
        filtered: list[Template] = []
        for tmpl in templates:
            if template_id is not None and getattr(tmpl, "id", None) == template_id:
                continue
            if template_title is not None and getattr(tmpl, "title", None) == template_title:
                continue
            filtered.append(tmpl)
        self.users[user_id]["custom_templates"] = filtered

    def set_least_template(self, user_id: int, template: Template) -> None:
        self.users.setdefault(user_id, {})["least_template"] = template

    def create_shared_template(self, template: Template) -> Template:
        return template

    def delete_shared_template(self, template_id: str) -> None:
        return None

    def copy_shared_template_to_user(
        self, user_id: int, template: Template
    ) -> Template:
        self.add_custom_template(user_id, template)
        return template


@dataclass(slots=True)
class TestApplicationBundle:
    """統合テストで利用するアプリケーション生成結果。"""

    application: DiscordApplication
    context: BootstrapContext
    repository: TemplateRepository


def create_test_application(
    *,
    config: AppConfig | None = None,
    repository_factory: Callable[[AppConfig], TemplateRepository] | None = None,
) -> TestApplicationBundle:
    """統合テスト向けに Discord アプリケーションを初期化する。"""

    app_config = config or AppConfig(
        discord=DiscordSettings(token="test-token"),
        firebase=FirebaseSettings(credentials_reference=":memory:"),
    )

    repository: TemplateRepository
    if repository_factory is not None:
        repository = repository_factory(app_config)
    else:
        repository = InMemoryTemplateRepository()

    context = bootstrap_application(
        config=app_config,
        log_level=logging.CRITICAL,
        repository_factory=lambda _: repository,
    )
    application = build_discord_application(context.injector)
    return TestApplicationBundle(application=application, context=context, repository=repository)


__all__ = [
    "InMemoryTemplateRepository",
    "TestApplicationBundle",
    "create_test_application",
]
