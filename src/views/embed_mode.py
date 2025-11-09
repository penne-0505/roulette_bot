"""互換性レイヤー: presentation.discord.views.embed_mode の再エクスポート。"""

from presentation.discord.components.embeds import (
    create_embed_mode_cancelled_embed,
    create_embed_mode_changed_embed,
    create_embed_mode_overview_embed,
)
from presentation.discord.views.embed_mode import EmbedModeView

__all__ = [
    "EmbedModeView",
    "create_embed_mode_cancelled_embed",
    "create_embed_mode_changed_embed",
    "create_embed_mode_overview_embed",
]
