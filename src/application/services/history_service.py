"""履歴・抽選設定に関するアプリケーションサービス。"""
from __future__ import annotations

from domain import AssignmentHistory, PairList, SelectionMode, Template
from domain.interfaces.repositories import TemplateRepository
from domain.services.selection_mode_service import coerce_selection_mode


class HistoryApplicationService:
    """履歴参照や抽選設定のユースケースを担うサービス。"""

    def __init__(self, repository: TemplateRepository) -> None:
        self._repository = repository

    def get_selection_mode(self) -> SelectionMode:
        """現在設定されている抽選モードを取得する。"""

        mode = self._repository.get_selection_mode()
        return coerce_selection_mode(mode)

    def get_recent_history(
        self,
        *,
        guild_id: int,
        template_title: str | None,
        limit: int,
    ) -> list[AssignmentHistory]:
        """抽選履歴を取得する。"""

        return self._repository.get_recent_history(
            guild_id=guild_id,
            template_title=template_title,
            limit=limit,
        )

    def save_history(
        self,
        *,
        guild_id: int,
        template: Template,
        pairs: PairList,
        selection_mode: SelectionMode,
    ) -> None:
        """抽選結果を履歴として保存する。"""

        self._repository.save_history(
            guild_id=guild_id,
            template=template,
            pairs=pairs,
            selection_mode=selection_mode,
        )

    def get_embed_mode(self) -> str:
        """抽選結果表示用の埋め込みモードを取得する。"""

        return self._repository.get_embed_mode()


__all__ = ["HistoryApplicationService"]
