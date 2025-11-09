"""互換性レイヤー: presentation.discord.views.selection_mode を再エクスポート。"""

from presentation.discord.components.embeds import create_selection_mode_overview_embed
from presentation.discord.views.selection_mode import SelectionModeView

__all__ = ["SelectionModeView", "create_selection_mode_overview_embed"]
