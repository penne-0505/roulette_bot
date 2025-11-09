"""ユーザー関連エンティティ。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .template import Template


@dataclass(slots=True)
class UserInfo:
    """ユーザー情報を表すデータモデル。"""

    id: int
    name: str
    least_template: Template | None = field(default=None)
    custom_templates: list[Template] = field(default_factory=list)
    shared_templates: list[Template] = field(default_factory=list)
    public_templates: list[Template] = field(default_factory=list)


__all__ = ["UserInfo"]
