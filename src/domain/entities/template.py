"""テンプレート関連のエンティティ。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from utils import generate_template_id


class TemplateScope(Enum):
    """テンプレートの共有範囲を示す列挙体。"""

    PRIVATE = "private"
    GUILD = "guild"
    PUBLIC = "public"


@dataclass(slots=True)
class Template:
    """テンプレートのデータモデル。"""

    title: str
    choices: list[str]
    scope: TemplateScope = TemplateScope.PRIVATE
    created_by: int | None = None
    guild_id: int | None = None
    template_id: str = field(default_factory=generate_template_id)
    updated_at: datetime | None = None


__all__ = ["Template", "TemplateScope"]
