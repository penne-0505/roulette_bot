"""Discord プレゼンテーション層で利用するサービス束。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from application.services.flow_service import AmidakujiFlowService
from application.services.history_service import HistoryApplicationService
from application.services.template_service import TemplateApplicationService
from domain.interfaces.repositories import TemplateRepository

if TYPE_CHECKING:  # pragma: no cover - 循環依存回避
    from data_interface import FlowController


@dataclass(slots=True)
class DiscordCommandUseCases:
    """スラッシュコマンドで利用するユースケースサービス群。"""

    template_service: TemplateApplicationService
    history_service: HistoryApplicationService
    amidakuji_flow_service: AmidakujiFlowService

    @classmethod
    def from_repository(
        cls, repository: TemplateRepository
    ) -> "DiscordCommandUseCases":
        """永続化リポジトリからユースケースサービスを組み立てる。"""

        template_service = TemplateApplicationService(repository)
        history_service = HistoryApplicationService(repository)
        flow_service = AmidakujiFlowService(template_service)
        return cls(
            template_service=template_service,
            history_service=history_service,
            amidakuji_flow_service=flow_service,
        )


@dataclass(slots=True)
class CommandRuntimeServices:
    """コマンド実行時にビューへ受け渡すサービス束。"""

    repository: TemplateRepository
    template_service: TemplateApplicationService
    history_service: HistoryApplicationService
    amidakuji_flow_service: AmidakujiFlowService
    flow: "FlowController" | None = None

    @classmethod
    def from_client(
        cls,
        *,
        repository: TemplateRepository,
        usecases: DiscordCommandUseCases,
    ) -> "CommandRuntimeServices":
        """クライアントが保持するユースケース群から実行時サービスを生成する。"""

        return cls(
            repository=repository,
            template_service=usecases.template_service,
            history_service=usecases.history_service,
            amidakuji_flow_service=usecases.amidakuji_flow_service,
        )


__all__ = ["CommandRuntimeServices", "DiscordCommandUseCases"]
