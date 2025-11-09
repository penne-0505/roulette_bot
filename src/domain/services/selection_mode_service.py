"""選択モードに関するドメインサービス。"""

from __future__ import annotations

from ..entities.history import SelectionMode


def coerce_selection_mode(value: SelectionMode | str) -> SelectionMode:
    """入力値を `SelectionMode` に正規化する。"""

    if isinstance(value, SelectionMode):
        return value
    normalized = str(value).lower()
    try:
        return SelectionMode(normalized)
    except ValueError as exc:  # pragma: no cover - 防御的ガード
        raise ValueError("Invalid selection mode") from exc


__all__ = ["coerce_selection_mode"]
