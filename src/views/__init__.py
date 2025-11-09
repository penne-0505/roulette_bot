"""後方互換性のためのビュー再エクスポート。"""

from presentation.discord.views.embed_mode import EmbedModeView
from presentation.discord.views.history_list import HistoryListView
from presentation.discord.views.selection_mode import SelectionModeView
from presentation.discord.views.template_list import TemplateListView
from presentation.discord.views.template_management import TemplateManagementView
from presentation.discord.views.template_sharing import TemplateSharingView

__all__ = [
    "EmbedModeView",
    "HistoryListView",
    "SelectionModeView",
    "TemplateListView",
    "TemplateManagementView",
    "TemplateSharingView",
]
