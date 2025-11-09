"""テンプレート関連のドメインサービス。"""

from __future__ import annotations

from collections.abc import Iterable

from ..entities.template import Template


def merge_templates(*template_lists: Iterable[Template]) -> list[Template]:
    """タイトル重複を除外しながらテンプレートを結合する。"""

    seen_titles: set[str] = set()
    merged: list[Template] = []
    for templates in template_lists:
        for template in templates:
            identifier = template.template_id or template.title
            if identifier in seen_titles:
                continue
            seen_titles.add(identifier)
            merged.append(template)
    return merged


__all__ = ["merge_templates"]
