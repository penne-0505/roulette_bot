"""ドメイン層で利用するリポジトリインタフェース。"""

from __future__ import annotations

from typing import Protocol

from .. import Template, UserInfo


class TemplateRepository(Protocol):
    """テンプレートおよびユーザーデータを扱うリポジトリ。"""

    def get_user(
        self,
        user_id: int,
        *,
        guild_id: int | None = None,
        include_shared: bool = True,
    ) -> UserInfo | None:
        ...

    def copy_shared_template_to_user(self, user_id: int, template: Template) -> Template:
        ...


__all__ = ["TemplateRepository"]
