from __future__ import annotations

from enum import Enum, auto
from math import ceil
from typing import Iterable

import discord

from models.model import Template


class TemplateCategory(Enum):
    PRIVATE = auto()
    GUILD = auto()
    PUBLIC = auto()


CATEGORY_LABELS = {
    TemplateCategory.PRIVATE: "個人テンプレート",
    TemplateCategory.GUILD: "サーバー共有",
    TemplateCategory.PUBLIC: "グローバル公開",
}


class TemplateListView(discord.ui.View):
    """テンプレートの一覧をカテゴリ別に切り替えて表示するビュー。"""

    PAGE_SIZE = 6

    def __init__(
        self,
        *,
        private_templates: Iterable[Template],
        guild_templates: Iterable[Template],
        public_templates: Iterable[Template],
    ) -> None:
        super().__init__(timeout=180)
        self.templates = {
            TemplateCategory.PRIVATE: list(private_templates),
            TemplateCategory.GUILD: list(guild_templates),
            TemplateCategory.PUBLIC: list(public_templates),
        }
        self.current_category: TemplateCategory = self._resolve_initial_category()
        self.current_page: int = 0

        self.category_buttons = [
            _CategoryButton(self, TemplateCategory.PRIVATE, "個人"),
            _CategoryButton(self, TemplateCategory.GUILD, "共有"),
            _CategoryButton(self, TemplateCategory.PUBLIC, "公開"),
        ]
        for button in self.category_buttons:
            self.add_item(button)

        self.prev_button = _PageButton(self, label="前へ", delta=-1)
        self.next_button = _PageButton(self, label="次へ", delta=1)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

        self.close_button = _CloseButton(self)
        self.add_item(self.close_button)

        self._update_components()

    def _resolve_initial_category(self) -> TemplateCategory:
        for category in TemplateCategory:
            if self.templates.get(category):
                return category
        return TemplateCategory.PRIVATE

    def _update_components(self) -> None:
        total_pages = self._total_pages_for(self.current_category)
        for button in self.category_buttons:
            button.disabled = button.category is self.current_category
            button.style = (
                discord.ButtonStyle.primary
                if button.category is self.current_category
                else discord.ButtonStyle.secondary
            )
        self.prev_button.disabled = self.current_page <= 0 or total_pages <= 1
        self.next_button.disabled = (
            total_pages <= 1 or self.current_page >= total_pages - 1
        )
        if not self.templates.get(self.current_category):
            self.prev_button.disabled = True
            self.next_button.disabled = True

    def _total_pages_for(self, category: TemplateCategory) -> int:
        items = self.templates.get(category, [])
        if not items:
            return 1
        return ceil(len(items) / self.PAGE_SIZE)

    def _current_items(self) -> list[Template]:
        items = self.templates.get(self.current_category, [])
        if not items:
            return []
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        return items[start:end]

    def _format_template(self, template: Template, index: int) -> str:
        choices = ", ".join(template.choices[:8]) if template.choices else "候補なし"
        if template.choices and len(template.choices) > 8:
            choices += ", ..."
        scope_note = ""
        if template.scope:
            scope_note = f"（scope: {template.scope.value}）"
        prefix = f"{index}. "
        return f"{prefix}**{template.title}**{scope_note}\n`{choices}`"

    def create_embed(self) -> discord.Embed:
        label = CATEGORY_LABELS[self.current_category]
        embed = discord.Embed(
            title="利用可能なテンプレート",
            description=f"カテゴリ: {label}",
            color=discord.Color.blurple(),
        )
        items = self._current_items()
        total_items = len(self.templates.get(self.current_category, []))
        if not items:
            embed.add_field(name="テンプレート", value="対象のテンプレートが見つかりません。", inline=False)
        else:
            lines = [
                self._format_template(template, index + 1 + self.current_page * self.PAGE_SIZE)
                for index, template in enumerate(items)
            ]
            embed.add_field(name="テンプレート", value="\n\n".join(lines), inline=False)

        total_pages = self._total_pages_for(self.current_category)
        embed.set_footer(
            text=(
                f"{label}: {total_items}件 | ページ {self.current_page + 1}/{total_pages}"
            )
        )
        return embed

    async def render(self, interaction: discord.Interaction) -> None:
        self._update_components()
        embed = self.create_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def set_category(self, category: TemplateCategory) -> None:
        if self.current_category is category:
            return
        self.current_category = category
        self.current_page = 0

    def turn_page(self, delta: int) -> None:
        total_pages = self._total_pages_for(self.current_category)
        self.current_page = max(0, min(self.current_page + delta, total_pages - 1))

    async def close(self, interaction: discord.Interaction) -> None:
        self.stop()
        for child in self.children:
            child.disabled = True
        embed = self.create_embed()
        embed.set_footer(text="表示を終了しました。")
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True


class _CategoryButton(discord.ui.Button):
    def __init__(
        self,
        view: TemplateListView,
        category: TemplateCategory,
        label: str,
    ) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_instance = view
        self.category = category

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view = self.view_instance
        view.set_category(self.category)
        await view.render(interaction)


class _PageButton(discord.ui.Button):
    def __init__(self, view: TemplateListView, *, label: str, delta: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.view_instance = view
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        view = self.view_instance
        if self.disabled:
            await interaction.response.defer(thinking=False)
            return
        view.turn_page(self.delta)
        await view.render(interaction)


class _CloseButton(discord.ui.Button):
    def __init__(self, view: TemplateListView) -> None:
        super().__init__(label="閉じる", style=discord.ButtonStyle.danger)
        self.view_instance = view

    async def callback(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        await self.view_instance.close(interaction)
