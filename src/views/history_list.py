"""互換性レイヤー: presentation.discord.views.history_list を再エクスポート。"""

from application.services.history_service import HistoryApplicationService
from presentation.discord.views.history_list import HistoryListView as _HistoryListView


class HistoryListView(_HistoryListView):
    """旧シグネチャ互換の履歴ビュー。"""

    def __init__(
        self,
        *,
        db_manager,
        guild_id: int,
        page_size: int = 5,
        template_title: str | None = None,
    ) -> None:
        history_service = HistoryApplicationService(db_manager)
        super().__init__(
            history_service=history_service,
            guild_id=guild_id,
            page_size=page_size,
            template_title=template_title,
        )


__all__ = ["HistoryListView"]
