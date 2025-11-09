from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import Binder, Injector, Module, provider, singleton

from app.config import AppConfig, load_config
from app.logging import configure_logging
from domain.interfaces.repositories import TemplateRepository
from presentation.discord.client import BotClient
from presentation.discord.services import DiscordCommandUseCases
from services.app_context import create_db_manager


@dataclass(frozen=True, slots=True)
class BootstrapContext:
    """アプリケーション初期化後の依存関係と設定値の束。"""

    config: AppConfig
    injector: Injector


def _default_repository_factory(config: AppConfig) -> TemplateRepository:
    return create_db_manager(config.firebase.credentials_reference)


class ApplicationModule(Module):
    """アプリケーション全体の依存関係を束ねる Injector モジュール。"""

    def __init__(
        self,
        config: AppConfig,
        *,
        repository_factory: Callable[[AppConfig], TemplateRepository] | None = None,
    ) -> None:
        self._config = config
        self._repository_factory = repository_factory or _default_repository_factory

    def configure(self, binder: Binder) -> None:  # pragma: no cover - 型保証のみ
        binder.bind(AppConfig, to=self._config, scope=singleton)

    @singleton
    @provider
    def provide_template_repository(self) -> TemplateRepository:
        return self._repository_factory(self._config)

    @singleton
    @provider
    def provide_command_usecases(
        self,
        repository: TemplateRepository,
    ) -> DiscordCommandUseCases:
        return DiscordCommandUseCases.from_repository(repository)

    @singleton
    @provider
    def provide_bot_client(
        self,
        repository: TemplateRepository,
        usecases: DiscordCommandUseCases,
    ) -> BotClient:
        return BotClient(db_manager=repository, usecases=usecases)


def bootstrap_application(
    *,
    config: AppConfig | None = None,
    env_file: str | Path | None = Path(".env"),
    log_level: int | str | None = None,
    logging_kwargs: Mapping[str, Any] | None = None,
    repository_factory: Callable[[AppConfig], TemplateRepository] | None = None,
    modules: Iterable[Module] | None = None,
) -> BootstrapContext:
    """設定読み込み・ロギング設定・依存解決をまとめて実行する。"""

    configure_logging(level=log_level, **dict(logging_kwargs or {}))

    app_config = config or load_config(env_file)

    base_module = ApplicationModule(app_config, repository_factory=repository_factory)
    module_list = [base_module, *(modules or [])]
    injector = Injector(module_list)

    return BootstrapContext(config=app_config, injector=injector)


__all__ = [
    "ApplicationModule",
    "BootstrapContext",
    "bootstrap_application",
]
