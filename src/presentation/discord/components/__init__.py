"""Discord プレゼンテーション用コンポーネント。"""

from .embeds import (
    create_embed_mode_cancelled_embed,
    create_embed_mode_changed_embed,
    create_embed_mode_overview_embed,
    create_selection_mode_cancelled_embed,
    create_selection_mode_changed_embed,
    create_selection_mode_overview_embed,
)

__all__ = [
    "create_embed_mode_cancelled_embed",
    "create_embed_mode_changed_embed",
    "create_embed_mode_overview_embed",
    "create_selection_mode_cancelled_embed",
    "create_selection_mode_changed_embed",
    "create_selection_mode_overview_embed",
]
